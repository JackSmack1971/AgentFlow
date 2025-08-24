"""Environment-specific configuration settings."""

from __future__ import annotations

from typing import Dict, Any
from .settings import (
    ApplicationSettings,
    SecuritySettings,
    DatabaseSettings,
    RedisSettings,
    Settings
)


class EnvironmentConfig:
    """Environment-specific configuration factory."""

    @staticmethod
    def get_development_config() -> Dict[str, Any]:
        """Development environment configuration."""
        return {
            "app": {
                "name": "AgentFlow API (Development)",
                "debug": True,
                "log_level": "DEBUG",
                "host": "127.0.0.1",
                "port": 8000,
                "environment": "dev",
                "max_body_size": 10 * 1024 * 1024,  # 10MB for dev
            },
            "security": {
                "cors_origins": [
                    "http://localhost:3000",
                    "http://127.0.0.1:3000",
                    "http://localhost:3001",
                    "http://localhost:8080"
                ],
                "rate_limit_per_minute": 1000,  # Higher limit for dev
                "rate_limit_burst": 100,
                "jwt_key_rotation_hours": 168,  # Weekly rotation in dev
                "security_log_level": "INFO",
                "security_max_failed_attempts": 10,  # More lenient in dev
                "security_lockout_duration_minutes": 5,
                "password_min_length": 8,  # Shorter passwords in dev
                "password_require_special_chars": False,  # Optional in dev
            },
            "database": {
                "pool_size": 5,  # Smaller pool for dev
                "pool_max_overflow": 10,
                "pool_timeout": 30.0,
                "pool_recycle": 1800,
                "pool_pre_ping": True,
                "echo": False,
            },
            "redis": {
                "db": 0,
                "socket_timeout": 5.0,
                "socket_connect_timeout": 5.0,
            }
        }

    @staticmethod
    def get_staging_config() -> Dict[str, Any]:
        """Staging environment configuration."""
        return {
            "app": {
                "name": "AgentFlow API (Staging)",
                "debug": False,
                "log_level": "INFO",
                "host": "0.0.0.0",
                "port": 8000,
                "environment": "staging",
                "max_body_size": 5 * 1024 * 1024,  # 5MB for staging
            },
            "security": {
                "cors_origins": [
                    "https://staging.agentflow.com",
                    "https://admin.staging.agentflow.com"
                ],
                "rate_limit_per_minute": 500,
                "rate_limit_burst": 50,
                "jwt_key_rotation_hours": 24,  # Daily rotation in staging
                "security_log_level": "WARNING",
                "security_max_failed_attempts": 5,
                "security_lockout_duration_minutes": 15,
                "password_min_length": 10,
                "password_require_special_chars": True,
            },
            "database": {
                "pool_size": 15,
                "pool_max_overflow": 30,
                "pool_timeout": 30.0,
                "pool_recycle": 1800,
                "pool_pre_ping": True,
                "echo": False,
            },
            "redis": {
                "db": 1,  # Separate DB for staging
                "socket_timeout": 5.0,
                "socket_connect_timeout": 5.0,
            }
        }

    @staticmethod
    def get_production_config() -> Dict[str, Any]:
        """Production environment configuration."""
        return {
            "app": {
                "name": "AgentFlow API",
                "debug": False,
                "log_level": "WARNING",
                "host": "0.0.0.0",
                "port": 8000,
                "environment": "prod",
                "max_body_size": 2 * 1024 * 1024,  # 2MB for prod
            },
            "security": {
                "cors_origins": [
                    "https://agentflow.com",
                    "https://admin.agentflow.com"
                ],
                "rate_limit_per_minute": 100,
                "rate_limit_burst": 20,
                "jwt_key_rotation_hours": 12,  # Twice daily rotation in prod
                "security_log_level": "ERROR",
                "security_max_failed_attempts": 3,
                "security_lockout_duration_minutes": 30,
                "password_min_length": 12,
                "password_require_special_chars": True,
            },
            "database": {
                "pool_size": 25,
                "pool_max_overflow": 50,
                "pool_timeout": 30.0,
                "pool_recycle": 1800,
                "pool_pre_ping": True,
                "echo": False,
            },
            "redis": {
                "db": 2,  # Separate DB for production
                "socket_timeout": 5.0,
                "socket_connect_timeout": 5.0,
            }
        }

    @classmethod
    def get_config_for_environment(cls, environment: str) -> Dict[str, Any]:
        """Get configuration for specific environment."""
        config_map = {
            "dev": cls.get_development_config,
            "development": cls.get_development_config,
            "staging": cls.get_staging_config,
            "prod": cls.get_production_config,
            "production": cls.get_production_config,
        }

        config_func = config_map.get(environment.lower())
        if not config_func:
            raise ValueError(f"Unknown environment: {environment}")

        return config_func()


class EnvironmentSettings:
    """Helper class to create settings with environment-specific overrides."""

    @staticmethod
    def create_settings_for_environment(
        environment: str,
        base_settings: Settings
    ) -> Settings:
        """Create settings instance with environment-specific overrides."""
        env_config = EnvironmentConfig.get_config_for_environment(environment)

        # Override settings with environment-specific values
        for section_name, section_config in env_config.items():
            section = getattr(base_settings, section_name)
            for key, value in section_config.items():
                setattr(section, key, value)

        return base_settings

    @staticmethod
    def validate_environment_settings(settings: Settings) -> None:
        """Validate settings for the specific environment."""
        environment = settings.app.environment

        # Production-specific validations
        if environment == "prod":
            if settings.app.debug:
                raise ValueError("Debug mode cannot be enabled in production")

            if settings.security.jwt_access_token_expire_minutes > 30:
                raise ValueError(
                    "Access token expiration too long for production security"
                )

            if settings.database.pool_size > 50:
                raise ValueError("Database pool size too large for production")

            if settings.security.rate_limit_per_minute > 200:
                raise ValueError("Rate limit too high for production")

        # Staging-specific validations
        elif environment == "staging":
            if settings.app.debug:
                raise ValueError("Debug mode should be disabled in staging")

            if settings.security.jwt_access_token_expire_minutes > 60:
                raise ValueError(
                    "Access token expiration too long for staging security"
                )

        # Development-specific validations
        elif environment == "dev":
            if settings.security.jwt_key_rotation_hours < 24:
                raise ValueError(
                    "JWT key rotation should be less frequent in development"
                )