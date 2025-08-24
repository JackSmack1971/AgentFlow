"""Tests for the configuration system."""

import os
import pytest
import base64
import secrets
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from apps.api.app.config import (
    ConfigurationFactory,
    SecretsManager,
    Settings,
    ApplicationSettings,
    SecuritySettings,
    DatabaseSettings,
    RedisSettings,
    get_settings,
    reload_settings,
    ConfigurationError
)


class TestConfigurationFactory:
    """Test the configuration factory."""

    def test_create_settings_development(self):
        """Test creating settings for development environment."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "dev",
            "SECRET_KEY": "test_secret_key_" + "a" * 32,
            "DATABASE_URL": "postgresql://user:pass@localhost/db",
            "REDIS_URL": "redis://localhost:6379",
            "QDRANT_URL": "http://localhost:6333",
            "ENCRYPTION_KEY": base64.b64encode(secrets.token_bytes(32)).decode(),
            "FERNET_KEY": base64.b64encode(secrets.token_bytes(32)).decode(),
        }):
            settings = ConfigurationFactory.create_settings("dev")

            assert settings.app.environment == "dev"
            assert settings.app.debug is True
            assert settings.app.log_level == "DEBUG"
            assert settings.security.rate_limit_per_minute == 1000

    def test_create_settings_production(self):
        """Test creating settings for production environment."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "prod",
            "SECRET_KEY": "test_secret_key_" + "a" * 32,
            "DATABASE_URL": "postgresql://user:pass@localhost/db",
            "REDIS_URL": "redis://localhost:6379",
            "QDRANT_URL": "http://localhost:6333",
            "ENCRYPTION_KEY": base64.b64encode(secrets.token_bytes(32)).decode(),
            "FERNET_KEY": base64.b64encode(secrets.token_bytes(32)).decode(),
        }):
            settings = ConfigurationFactory.create_settings("prod")

            assert settings.app.environment == "prod"
            assert settings.app.debug is False
            assert settings.app.log_level == "WARNING"
            assert settings.security.rate_limit_per_minute == 100

    def test_create_settings_staging(self):
        """Test creating settings for staging environment."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "staging",
            "SECRET_KEY": "test_secret_key_" + "a" * 32,
            "DATABASE_URL": "postgresql://user:pass@localhost/db",
            "REDIS_URL": "redis://localhost:6379",
            "QDRANT_URL": "http://localhost:6333",
            "ENCRYPTION_KEY": base64.b64encode(secrets.token_bytes(32)).decode(),
            "FERNET_KEY": base64.b64encode(secrets.token_bytes(32)).decode(),
        }):
            settings = ConfigurationFactory.create_settings("staging")

            assert settings.app.environment == "staging"
            assert settings.app.debug is False
            assert settings.app.log_level == "INFO"
            assert settings.security.rate_limit_per_minute == 500

    def test_invalid_environment(self):
        """Test creating settings with invalid environment."""
        with pytest.raises(ValueError, match="Unknown environment"):
            ConfigurationFactory.create_settings("invalid")

    def test_missing_required_secrets(self):
        """Test that missing secrets raise ConfigurationError."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "dev",
            "SECRET_KEY": "test_secret_key_" + "a" * 32,
            # Missing required secrets
        }, clear=True):
            with pytest.raises(ConfigurationError, match="ENCRYPTION_KEY must be set"):
                ConfigurationFactory.create_settings("dev", validate_secrets=True)

    def test_invalid_encryption_key(self):
        """Test that invalid encryption key raises ConfigurationError."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "dev",
            "SECRET_KEY": "test_secret_key_" + "a" * 32,
            "DATABASE_URL": "postgresql://user:pass@localhost/db",
            "REDIS_URL": "redis://localhost:6379",
            "QDRANT_URL": "http://localhost:6333",
            "ENCRYPTION_KEY": "invalid_key",
            "FERNET_KEY": base64.b64encode(secrets.token_bytes(32)).decode(),
        }):
            with pytest.raises(ConfigurationError, match="Invalid encryption key format"):
                ConfigurationFactory.create_settings("dev", validate_secrets=True)


class TestSecretsManager:
    """Test the secrets manager."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "dev",
            "SECRET_KEY": "test_secret_key_" + "a" * 32,
            "DATABASE_URL": "postgresql://user:pass@localhost/db",
            "REDIS_URL": "redis://localhost:6379",
            "QDRANT_URL": "http://localhost:6333",
            "ENCRYPTION_KEY": base64.b64encode(secrets.token_bytes(32)).decode(),
            "FERNET_KEY": base64.b64encode(secrets.token_bytes(32)).decode(),
        }):
            self.settings = ConfigurationFactory.create_settings("dev")
            self.secrets_manager = SecretsManager(self.settings)

    def test_jwt_key_rotation(self):
        """Test JWT key rotation functionality."""
        # Get initial key
        key1 = self.secrets_manager.get_current_jwt_key()
        assert len(key1) >= 64  # Should be a long secure key

        # Force rotation by manipulating timestamps
        self.secrets_manager._rotation_timestamps["jwt"] = datetime.utcnow() - timedelta(hours=25)

        # Get new key
        key2 = self.secrets_manager.get_current_jwt_key()
        assert key1 != key2  # Should be different

    def test_previous_jwt_key(self):
        """Test getting previous JWT key."""
        # Initially no previous key
        assert self.secrets_manager.get_previous_jwt_key() is None

        # Get current key and force rotation
        key1 = self.secrets_manager.get_current_jwt_key()
        self.secrets_manager._rotation_timestamps["jwt"] = datetime.utcnow() - timedelta(hours=25)

        # Get new key
        key2 = self.secrets_manager.get_current_jwt_key()
        previous_key = self.secrets_manager.get_previous_jwt_key()

        assert previous_key == key1

    def test_secret_format_validation(self):
        """Test secret format validation."""
        # Valid secret
        assert self.secrets_manager.validate_secret_format("test_secret", "a" * 32)

        # Invalid secrets
        with pytest.raises(ConfigurationError, match="cannot be empty"):
            self.secrets_manager.validate_secret_format("test_secret", "")

        with pytest.raises(ConfigurationError, match="must be at least 32 characters"):
            self.secrets_manager.validate_secret_format("test_secret", "short")


class TestSettingsValidation:
    """Test settings validation."""

    def test_production_settings_validation(self):
        """Test production-specific settings validation."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "prod",
            "SECRET_KEY": "test_secret_key_" + "a" * 32,
            "DATABASE_URL": "postgresql://user:pass@localhost/db",
            "REDIS_URL": "redis://localhost:6379",
            "QDRANT_URL": "http://localhost:6333",
            "ENCRYPTION_KEY": base64.b64encode(secrets.token_bytes(32)).decode(),
            "FERNET_KEY": base64.b64encode(secrets.token_bytes(32)).decode(),
        }):
            # Should work with valid production settings
            settings = ConfigurationFactory.create_settings("prod")
            assert settings.app.debug is False

    def test_production_debug_mode_error(self):
        """Test that debug mode is rejected in production."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "prod",
            "SECRET_KEY": "test_secret_key_" + "a" * 32,
            "DATABASE_URL": "postgresql://user:pass@localhost/db",
            "REDIS_URL": "redis://localhost:6379",
            "QDRANT_URL": "http://localhost:6333",
            "ENCRYPTION_KEY": base64.b64encode(secrets.token_bytes(32)).decode(),
            "FERNET_KEY": base64.b64encode(secrets.token_bytes(32)).decode(),
            "DEBUG": "true",
        }):
            with pytest.raises(ValueError, match="Debug mode cannot be enabled in production"):
                ConfigurationFactory.create_settings("prod")

    def test_database_url_validation(self):
        """Test database URL validation."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "dev",
            "SECRET_KEY": "test_secret_key_" + "a" * 32,
            "DATABASE_URL": "mysql://user:pass@localhost/db",  # Invalid for PostgreSQL
            "REDIS_URL": "redis://localhost:6379",
            "QDRANT_URL": "http://localhost:6333",
            "ENCRYPTION_KEY": base64.b64encode(secrets.token_bytes(32)).decode(),
            "FERNET_KEY": base64.b64encode(secrets.token_bytes(32)).decode(),
        }):
            with pytest.raises(ValueError, match="Database URL must use PostgreSQL"):
                ConfigurationFactory.create_settings("dev")

    def test_redis_url_validation(self):
        """Test Redis URL validation."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "dev",
            "SECRET_KEY": "test_secret_key_" + "a" * 32,
            "DATABASE_URL": "postgresql://user:pass@localhost/db",
            "REDIS_URL": "invalid://localhost:6379",  # Invalid Redis URL
            "QDRANT_URL": "http://localhost:6333",
            "ENCRYPTION_KEY": base64.b64encode(secrets.token_bytes(32)).decode(),
            "FERNET_KEY": base64.b64encode(secrets.token_bytes(32)).decode(),
        }):
            with pytest.raises(ValueError, match="Redis URL must start with redis://"):
                ConfigurationFactory.create_settings("dev")


class TestGlobalFunctions:
    """Test global configuration functions."""

    def test_get_settings_caching(self):
        """Test that get_settings uses caching."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "dev",
            "SECRET_KEY": "test_secret_key_" + "a" * 32,
            "DATABASE_URL": "postgresql://user:pass@localhost/db",
            "REDIS_URL": "redis://localhost:6379",
            "QDRANT_URL": "http://localhost:6333",
            "ENCRYPTION_KEY": base64.b64encode(secrets.token_bytes(32)).decode(),
            "FERNET_KEY": base64.b64encode(secrets.token_bytes(32)).decode(),
        }):
            settings1 = get_settings()
            settings2 = get_settings()

            # Should return the same instance due to caching
            assert settings1 is settings2

    def test_reload_settings(self):
        """Test settings reloading."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "dev",
            "SECRET_KEY": "test_secret_key_" + "a" * 32,
            "DATABASE_URL": "postgresql://user:pass@localhost/db",
            "REDIS_URL": "redis://localhost:6379",
            "QDRANT_URL": "http://localhost:6333",
            "ENCRYPTION_KEY": base64.b64encode(secrets.token_bytes(32)).decode(),
            "FERNET_KEY": base64.b64encode(secrets.token_bytes(32)).decode(),
        }):
            settings1 = get_settings()
            settings2 = reload_settings()

            # Should return different instances after reload
            assert settings1 is not settings2


class TestEnvironmentSpecificSettings:
    """Test environment-specific settings."""

    def test_development_cors_origins(self):
        """Test development CORS origins."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "dev",
            "SECRET_KEY": "test_secret_key_" + "a" * 32,
            "DATABASE_URL": "postgresql://user:pass@localhost/db",
            "REDIS_URL": "redis://localhost:6379",
            "QDRANT_URL": "http://localhost:6333",
            "ENCRYPTION_KEY": base64.b64encode(secrets.token_bytes(32)).decode(),
            "FERNET_KEY": base64.b64encode(secrets.token_bytes(32)).decode(),
        }):
            settings = ConfigurationFactory.create_settings("dev")

            expected_origins = [
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "http://localhost:3001",
                "http://localhost:8080"
            ]
            assert settings.security.cors_origins == expected_origins

    def test_production_cors_origins(self):
        """Test production CORS origins."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "prod",
            "SECRET_KEY": "test_secret_key_" + "a" * 32,
            "DATABASE_URL": "postgresql://user:pass@localhost/db",
            "REDIS_URL": "redis://localhost:6379",
            "QDRANT_URL": "http://localhost:6333",
            "ENCRYPTION_KEY": base64.b64encode(secrets.token_bytes(32)).decode(),
            "FERNET_KEY": base64.b64encode(secrets.token_bytes(32)).decode(),
        }):
            settings = ConfigurationFactory.create_settings("prod")

            expected_origins = [
                "https://agentflow.com",
                "https://admin.agentflow.com"
            ]
            assert settings.security.cors_origins == expected_origins

    def test_database_pool_sizes_by_environment(self):
        """Test database pool sizes vary by environment."""
        environments = ["dev", "staging", "prod"]
        expected_pool_sizes = [5, 15, 25]

        for env, expected_size in zip(environments, expected_pool_sizes):
            with patch.dict(os.environ, {
                "ENVIRONMENT": env,
                "SECRET_KEY": "test_secret_key_" + "a" * 32,
                "DATABASE_URL": "postgresql://user:pass@localhost/db",
                "REDIS_URL": "redis://localhost:6379",
                "QDRANT_URL": "http://localhost:6333",
                "ENCRYPTION_KEY": base64.b64encode(secrets.token_bytes(32)).decode(),
                "FERNET_KEY": base64.b64encode(secrets.token_bytes(32)).decode(),
            }):
                settings = ConfigurationFactory.create_settings(env)
                assert settings.database.pool_size == expected_size