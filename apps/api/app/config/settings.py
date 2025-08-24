"""Base settings configuration with Pydantic validation and security features."""

from __future__ import annotations

import secrets
from datetime import timedelta
from typing import List, Optional

from pydantic import Field, ValidationError, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class SecuritySettings(BaseSettings):
    """Security-related configuration settings."""

    model_config = SettingsConfigDict(env_file=".env", extra="forbid")

    # JWT Configuration
    jwt_secret_key: Optional[str] = Field(default=None, description="Primary JWT secret key")
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_access_token_expire_minutes: int = Field(
        default=15, description="Access token expiration in minutes"
    )
    jwt_refresh_token_expire_days: int = Field(
        default=7, description="Refresh token expiration in days"
    )
    jwt_key_rotation_hours: int = Field(
        default=24, description="JWT key rotation interval in hours"
    )

    # Encryption Keys
    encryption_key: str = Field(..., description="AES-256 encryption key (base64 encoded)")
    fernet_key: str = Field(..., description="Fernet encryption key for sensitive data")

    # Security Headers and Policies
    cors_origins: List[str] = Field(
        default=["http://localhost:3000"],
        description="Allowed CORS origins"
    )
    cors_credentials: bool = Field(default=True, description="Allow credentials in CORS")
    cors_methods: List[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        description="Allowed CORS methods"
    )
    cors_headers: List[str] = Field(
        default=["*"],
        description="Allowed CORS headers"
    )

    # Rate Limiting
    rate_limit_per_minute: int = Field(
        default=100,
        description="Rate limit requests per minute per IP"
    )
    rate_limit_burst: int = Field(
        default=20,
        description="Rate limit burst capacity"
    )

    # Security Monitoring
    security_log_level: str = Field(
        default="WARNING",
        description="Security event log level"
    )
    security_max_failed_attempts: int = Field(
        default=5,
        description="Max failed authentication attempts before lockout"
    )
    security_lockout_duration_minutes: int = Field(
        default=30,
        description="Account lockout duration in minutes"
    )

    # Password Policy
    password_min_length: int = Field(default=12, description="Minimum password length")
    password_require_uppercase: bool = Field(
        default=True,
        description="Require uppercase letters in password"
    )
    password_require_lowercase: bool = Field(
        default=True,
        description="Require lowercase letters in password"
    )
    password_require_numbers: bool = Field(
        default=True,
        description="Require numbers in password"
    )
    password_require_special_chars: bool = Field(
        default=True,
        description="Require special characters in password"
    )

    # Legacy/Compatibility Fields (from .env file)
    database_url: Optional[str] = Field(default=None, description="Legacy database URL field")
    test_database_url: Optional[str] = Field(default=None, description="Legacy test database URL field")
    redis_url: Optional[str] = Field(default=None, description="Legacy Redis URL field")
    app_name: Optional[str] = Field(default=None, description="Legacy app name field")
    secret_key: Optional[str] = Field(default=None, description="Legacy secret key field")
    debug: Optional[str] = Field(default=None, description="Legacy debug field")
    log_level: Optional[str] = Field(default=None, description="Legacy log level field")
    development_mode: Optional[str] = Field(default=None, description="Legacy development mode field")
    environment: Optional[str] = Field(default=None, description="Legacy environment field")
    api_prefix: Optional[str] = Field(default=None, description="Legacy API prefix field")
    reload_on_change: Optional[str] = Field(default=None, description="Legacy reload on change field")

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_jwt_secret_key(cls, v: Optional[str]) -> str:
        """Validate JWT secret key length and complexity."""
        if v is None:
            import secrets
            v = secrets.token_urlsafe(64)  # Generate secure random key
        if len(v) < 32:
            raise ValueError("JWT secret key must be at least 32 characters long")
        return v

    @field_validator("encryption_key")
    @classmethod
    def validate_encryption_key(cls, v: str) -> str:
        """Validate AES encryption key format."""
        import base64
        try:
            decoded = base64.b64decode(v)
            if len(decoded) != 32:
                raise ValueError("Encryption key must be 32 bytes (base64 encoded)")
        except Exception as e:
            raise ValueError(f"Invalid encryption key format: {e}")
        return v

    @field_validator("fernet_key")
    @classmethod
    def validate_fernet_key(cls, v: str) -> str:
        """Validate Fernet key format."""
        import base64
        try:
            decoded = base64.b64decode(v)
            if len(decoded) != 32:
                raise ValueError("Fernet key must be 32 bytes (base64 encoded)")
        except Exception as e:
            raise ValueError(f"Invalid Fernet key format: {e}")
        return v

    @field_validator("cors_origins")
    @classmethod
    def validate_cors_origins(cls, v: List[str]) -> List[str]:
        """Validate CORS origins format."""
        from urllib.parse import urlparse
        for origin in v:
            parsed = urlparse(origin)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError(f"Invalid CORS origin format: {origin}")
        return v


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    model_config = SettingsConfigDict(env_file=".env", extra="forbid")

    # Database Connection
    url: Optional[str] = Field(default=None, description="Database connection URL")
    pool_size: int = Field(default=10, description="Database connection pool size")
    pool_max_overflow: int = Field(
        default=20,
        description="Maximum overflow connections"
    )
    pool_timeout: float = Field(
        default=30.0,
        description="Connection timeout in seconds"
    )
    pool_recycle: int = Field(
        default=1800,
        description="Connection recycle time in seconds"
    )
    pool_pre_ping: bool = Field(
        default=True,
        description="Enable connection pre-ping"
    )
    echo: bool = Field(default=False, description="Enable SQL echo for debugging")

    # Legacy/Compatibility Fields (from .env file)
    database_url: Optional[str] = Field(default=None, description="Legacy database URL field")
    test_database_url: Optional[str] = Field(default=None, description="Legacy test database URL field")
    redis_url: Optional[str] = Field(default=None, description="Legacy Redis URL field")
    app_name: Optional[str] = Field(default=None, description="Legacy app name field")
    secret_key: Optional[str] = Field(default=None, description="Legacy secret key field")
    debug: Optional[str] = Field(default=None, description="Legacy debug field")
    log_level: Optional[str] = Field(default=None, description="Legacy log level field")
    development_mode: Optional[str] = Field(default=None, description="Legacy development mode field")
    environment: Optional[str] = Field(default=None, description="Legacy environment field")
    encryption_key: Optional[str] = Field(default=None, description="Legacy encryption key field")
    fernet_key: Optional[str] = Field(default=None, description="Legacy Fernet key field")
    api_prefix: Optional[str] = Field(default=None, description="Legacy API prefix field")
    reload_on_change: Optional[str] = Field(default=None, description="Legacy reload on change field")

    @field_validator("url")
    @classmethod
    def validate_database_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate database URL format."""
        if v is None:
            return v
        if not v.startswith(("postgresql://", "postgresql+psycopg://")):
            raise ValueError("Database URL must use PostgreSQL")
        return v

    @field_validator("pool_size", "pool_max_overflow")
    @classmethod
    def validate_pool_sizes(cls, v: int) -> int:
        """Validate connection pool sizes."""
        if v < 1:
            raise ValueError("Pool size must be at least 1")
        if v > 100:
            raise ValueError("Pool size cannot exceed 100")
        return v


class RedisSettings(BaseSettings):
    """Redis configuration settings."""

    model_config = SettingsConfigDict(env_file=".env", extra="forbid")

    url: Optional[str] = Field(default=None, description="Redis connection URL")
    cluster_nodes: Optional[List[str]] = Field(
        default=None,
        description="Redis cluster nodes"
    )
    db: int = Field(default=0, description="Redis database number")
    password: Optional[str] = Field(default=None, description="Redis password")
    socket_timeout: Optional[float] = Field(
        default=5.0,
        description="Redis socket timeout"
    )
    socket_connect_timeout: Optional[float] = Field(
        default=5.0,
        description="Redis socket connect timeout"
    )

    # Legacy/Compatibility Fields (from .env file)
    database_url: Optional[str] = Field(default=None, description="Legacy database URL field")
    test_database_url: Optional[str] = Field(default=None, description="Legacy test database URL field")
    redis_url: Optional[str] = Field(default=None, description="Legacy Redis URL field")
    app_name: Optional[str] = Field(default=None, description="Legacy app name field")
    secret_key: Optional[str] = Field(default=None, description="Legacy secret key field")
    debug: Optional[str] = Field(default=None, description="Legacy debug field")
    log_level: Optional[str] = Field(default=None, description="Legacy log level field")
    development_mode: Optional[str] = Field(default=None, description="Legacy development mode field")
    environment: Optional[str] = Field(default=None, description="Legacy environment field")
    encryption_key: Optional[str] = Field(default=None, description="Legacy encryption key field")
    fernet_key: Optional[str] = Field(default=None, description="Legacy Fernet key field")
    api_prefix: Optional[str] = Field(default=None, description="Legacy API prefix field")
    reload_on_change: Optional[str] = Field(default=None, description="Legacy reload on change field")

    @field_validator("url")
    @classmethod
    def validate_redis_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate Redis URL format."""
        if v is None:
            return v
        if not v.startswith("redis://"):
            raise ValueError("Redis URL must start with redis://")
        return v


class ApplicationSettings(BaseSettings):
    """Main application configuration settings."""

    model_config = SettingsConfigDict(env_file=".env", extra="forbid")

    # Basic Application Settings
    name: str = Field(default="AgentFlow API", description="Application name")
    version: str = Field(default="1.0.0", description="Application version")
    environment: str = Field(
        default="dev",
        description="Environment: dev, staging, prod"
    )
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

    # API Configuration
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    api_prefix: str = Field(default="/api/v1", description="API prefix")
    openapi_url: str = Field(default="/openapi.json", description="OpenAPI URL")

    # File Upload Limits
    max_body_size: int = Field(
        default=1024 * 1024,
        description="Maximum request body size in bytes"
    )

    # Service Timeouts
    http_timeout: float = Field(default=5.0, description="HTTP client timeout")
    http_max_retries: int = Field(default=3, description="HTTP client max retries")

    # External Services
    qdrant_url: str = Field(..., description="Qdrant service URL")
    r2r_base_url: str = Field(
        default="http://localhost:7272",
        description="R2R service base URL"
    )
    r2r_api_key: Optional[str] = Field(
        default=None,
        description="R2R API key"
    )

    # Agent Configuration
    agent_run_timeout_seconds: int = Field(
        default=30,
        description="Agent run timeout in seconds"
    )
    agent_retry_max_attempts: int = Field(
        default=3,
        description="Maximum agent retry attempts"
    )
    agent_retry_backoff_seconds: float = Field(
        default=1.0,
        description="Agent retry backoff in seconds"
    )

    # Memory Configuration
    memory_api_timeout: float = Field(
        default=5.0,
        description="Memory API timeout"
    )
    memory_api_retries: int = Field(
        default=1,
        description="Memory API retry attempts"
    )

    # Legacy/Compatibility Fields (from .env file)
    app_name: Optional[str] = Field(default=None, description="Legacy app name field")
    secret_key: Optional[str] = Field(default=None, description="Legacy secret key field")
    database_url: Optional[str] = Field(default=None, description="Legacy database URL field")
    test_database_url: Optional[str] = Field(default=None, description="Legacy test database URL field")
    redis_url: Optional[str] = Field(default=None, description="Legacy Redis URL field")
    development_mode: Optional[str] = Field(default=None, description="Legacy development mode field")
    encryption_key: Optional[str] = Field(default=None, description="Legacy encryption key field")
    fernet_key: Optional[str] = Field(default=None, description="Legacy Fernet key field")
    reload_on_change: Optional[str] = Field(default=None, description="Legacy reload on change field")

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment value."""
        allowed = {"dev", "staging", "prod"}
        if v not in allowed:
            raise ValueError(f"Environment must be one of: {allowed}")
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        import logging
        try:
            logging.getLevelName(v.upper())
        except (ValueError, TypeError):
            raise ValueError(f"Invalid log level: {v}")
        return v.upper()


class Settings(BaseSettings):
    """Complete application settings combining all configuration sections."""

    model_config = SettingsConfigDict(env_file=".env", extra="forbid")

    # Nested settings objects
    app: ApplicationSettings
    security: SecuritySettings
    database: DatabaseSettings
    redis: RedisSettings

    @model_validator(mode="after")
    def validate_settings_consistency(self) -> "Settings":
        """Validate consistency across all settings."""
        # In production, ensure secure defaults
        if self.app.environment == "prod":
            if self.app.debug:
                raise ValueError("Debug mode cannot be enabled in production")

            if self.security.jwt_access_token_expire_minutes > 30:
                raise ValueError("Access token expiration too long for production")

            if self.database.pool_size > 50:
                raise ValueError("Database pool size too large for production")

        return self

    # Legacy/Compatibility Fields (from .env file)
    database_url: Optional[str] = Field(default=None, description="Legacy database URL field")
    test_database_url: Optional[str] = Field(default=None, description="Legacy test database URL field")
    redis_url: Optional[str] = Field(default=None, description="Legacy Redis URL field")
    app_name: Optional[str] = Field(default=None, description="Legacy app name field")
    secret_key: Optional[str] = Field(default=None, description="Legacy secret key field")
    debug: Optional[str] = Field(default=None, description="Legacy debug field")
    log_level: Optional[str] = Field(default=None, description="Legacy log level field")
    development_mode: Optional[str] = Field(default=None, description="Legacy development mode field")
    environment: Optional[str] = Field(default=None, description="Legacy environment field")
    encryption_key: Optional[str] = Field(default=None, description="Legacy encryption key field")
    fernet_key: Optional[str] = Field(default=None, description="Legacy Fernet key field")
    api_prefix: Optional[str] = Field(default=None, description="Legacy API prefix field")
    reload_on_change: Optional[str] = Field(default=None, description="Legacy reload on change field")


# Global settings instance - lazy loaded
_settings_instance = None

def get_settings_instance() -> Settings:
    """Get the global settings instance, creating it if necessary."""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings(
            app=ApplicationSettings(),
            security=SecuritySettings(),
            database=DatabaseSettings(),
            redis=RedisSettings()
        )
    return _settings_instance