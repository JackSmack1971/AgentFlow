"""Security test fixtures and configuration.

This module provides test fixtures specifically for security testing.
It sets up real authentication, database connections, and security components
WITHOUT the mocked authentication that bypasses security checks.
"""

import os
import pathlib
import sys
import uuid
from datetime import datetime, timedelta
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Security-specific test settings (must be set before importing app modules)
os.environ["DATABASE_URL"] = "postgresql+asyncpg://test_user:test_pass@localhost:5432/test_security_db"
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")  # Use separate Redis DB for security tests
os.environ.setdefault("SECRET_KEY", "test_security_secret_key_32_chars_min")
os.environ.setdefault("JWT_SECRET_KEY", "test_jwt_secret_key_32_chars_min_length")
os.environ.setdefault("FERNET_KEY", "YWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWE=")
os.environ.setdefault("ENVIRONMENT", "test")

# Additional required environment variables for security tests
os.environ.setdefault("QDRANT_URL", "http://localhost:6333")
os.environ.setdefault("OPENAI_API_KEY", "test_key")
os.environ.setdefault("ENCRYPTION_KEY", "YmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmI=")
os.environ.setdefault("APP_NAME", "AgentFlow Security Test")
os.environ.setdefault("LOG_LEVEL", "INFO")
os.environ.pop("DEBUG", None)
os.environ.pop("DEVELOPMENT_MODE", None)
os.environ.pop("API_PREFIX", None)
os.environ.pop("RELOAD_ON_CHANGE", None)
os.environ.pop("TEST_DATABASE_URL", None)

# Add the project root to the Python path
sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))

from apps.api.app.core.settings import get_settings
from apps.api.app.database import get_db
from apps.api.app.db.base import Base
from apps.api.app.db.models import User
from apps.api.app.main import app
from apps.api.app.services.auth import AuthService
from apps.api.app.utils.encryption import get_encryption_manager
from apps.api.app.utils.password import hash_password, verify_password
from apps.api.app.services.rate_limiting_service import (
    RateLimitingService,
    RateLimitConfig,
    RateLimitStrategy
)
from apps.api.app.services.security_monitoring import (
    SecurityMonitoringService,
    MonitoringConfig
)

from apps.api.app.utils.rsa import generate_rsa_key_pair

settings = get_settings()

# Create test database engine
engine = create_engine(settings.database_url)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def test_db_engine():
    """Create test database engine for security tests."""
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(test_db_engine):
    """Provide database session for tests."""
    connection = test_db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    """Create test client with real authentication."""
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
async def auth_service(db_session):
    """Provide AuthService instance for testing."""
    return AuthService(db_session)


@pytest.fixture
async def encryption_manager():
    """Provide encryption manager for testing."""
    return get_encryption_manager()


@pytest.fixture
async def test_user(db_session, auth_service):
    """Create a test user for authentication testing."""
    user_email = f"test_{uuid.uuid4()}@example.com"
    user_password = "TestPassword123!"

    # Create user through auth service
    otp_secret = await auth_service.register_user(user_email, user_password)

    # Get the created user
    user = db_session.query(User).filter(User.email == user_email).first()

    yield {
        "user": user,
        "email": user_email,
        "password": user_password,
        "otp_secret": otp_secret
    }

    # Cleanup
    db_session.query(User).filter(User.email == user_email).delete()
    db_session.commit()


@pytest.fixture
async def authenticated_user(client, test_user, auth_service):
    """Create authenticated user with valid tokens."""
    # Authenticate the user
    await auth_service.authenticate_user(
        test_user["email"],
        test_user["password"],
        test_user["otp_secret"]
    )

    # Generate tokens
    from apps.api.app.services.auth import create_access_token, create_refresh_token

    access_token = await create_access_token(test_user["email"])
    refresh_token = await create_refresh_token(test_user["email"])

    yield {
        **test_user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "auth_header": f"Bearer {access_token}"
    }


@pytest.fixture
def expired_token():
    """Generate an expired JWT token for testing."""
    from apps.api.app.services.auth import create_access_token
    import jwt
    import time

    # Create token that expires immediately
    expired_payload = {
        "sub": "expired@example.com",
        "exp": int(time.time()) - 3600,  # Expired 1 hour ago
        "iat": int(time.time()) - 7200,
        "type": "access"
    }

    return jwt.encode(expired_payload, settings.secret_key, algorithm="HS256")


@pytest.fixture
def invalid_token():
    """Generate an invalid JWT token for testing."""
    return "invalid.jwt.token.here"


@pytest.fixture
def malformed_token():
    """Generate a malformed JWT token for testing."""
    return "malformed_token_without_proper_structure"


@pytest.fixture
async def locked_user(db_session, test_user):
    """Create a user with locked account for testing."""
    user = test_user["user"]

    # Simulate failed login attempts
    for _ in range(5):
        user.record_failed_login()

    # Ensure account is locked
    assert user.is_account_locked()

    db_session.commit()

    yield user


@pytest.fixture
async def user_with_failed_attempts(db_session, test_user):
    """Create a user with some failed login attempts."""
    user = test_user["user"]

    # Add 3 failed attempts (below lock threshold)
    for _ in range(3):
        user.record_failed_login()

    db_session.commit()

    yield user


# Security test utilities

class SecurityTestClient(TestClient):
    """Extended TestClient with security testing utilities."""

    def request_with_ip(self, ip_address="127.0.0.1", *args, **kwargs):
        """Make request with specific IP address."""
        headers = kwargs.get("headers", {})
        headers["X-Forwarded-For"] = ip_address
        kwargs["headers"] = headers
        return self.request(*args, **kwargs)

    def rapid_requests(self, url, count=10, interval=0.1):
        """Make rapid requests for rate limiting tests."""
        import time
        responses = []
        for _ in range(count):
            response = self.get(url)
            responses.append(response)
            time.sleep(interval)
        return responses


@pytest.fixture
def security_client(client):
    """Provide SecurityTestClient for security testing."""
    return SecurityTestClient(app)


@pytest_asyncio.fixture(scope="session")
async def rsa_keys(tmp_path_factory):
    """Generate RSA key pair for JWT tests."""
    key_dir = tmp_path_factory.mktemp("keys")
    private_path = key_dir / "jwt_private.pem"
    public_path = key_dir / "jwt_public.pem"
    await generate_rsa_key_pair(str(private_path), str(public_path))
    return str(private_path), str(public_path)


# Redis fixtures for security testing

@pytest.fixture
async def redis_client():
    """Provide Redis client for security state testing."""
    import redis.asyncio as redis

    client = redis.Redis.from_url(settings.redis_url)

    # Clear security-related keys
    await client.flushdb()

    yield client

    # Cleanup
    await client.flushdb()
    await client.close()


@pytest.fixture
def rate_limit_config():
    """Provide rate limiting configuration for testing."""
    return RateLimitConfig(
        requests_per_minute=100,
        burst_limit=20,
        window_seconds=60,
        strategy=RateLimitStrategy.SLIDING_WINDOW
    )


@pytest.fixture
def rate_limiting_service(redis_client, rate_limit_config):
    """Provide rate limiting service for testing."""
    return RateLimitingService(redis_client, rate_limit_config)


@pytest.fixture
def monitoring_config():
    """Provide security monitoring configuration for testing."""
    return MonitoringConfig(
        alert_thresholds={
            EventType.SUSPICIOUS_LOGIN: 3,
            EventType.RATE_LIMIT_EXCEEDED: 5,
            EventType.UNAUTHORIZED_ACCESS: 1
        },
        metrics_retention_days=30,
        enable_real_time_alerts=True,
        anomaly_detection_enabled=True
    )


@pytest.fixture
def security_monitoring_service(redis_client, monitoring_config):
    """Provide security monitoring service for testing."""
    return SecurityMonitoringService(redis_client, monitoring_config)


# Import EventType for fixtures
from apps.api.app.services.security_monitoring import EventType