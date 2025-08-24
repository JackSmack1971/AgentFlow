"""Configuration factory and utilities for AgentFlow API."""

from __future__ import annotations

import os
import logging
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Optional, Dict, Any

from .settings import (
    Settings,
    ApplicationSettings,
    SecuritySettings,
    DatabaseSettings,
    RedisSettings,
    get_settings_instance
)
from .environments import EnvironmentSettings

# Configure logging for configuration module
logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when configuration validation fails."""
    pass


class SecretsManager:
    """Manages secure secrets with rotation capabilities."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._jwt_keys: Dict[str, Dict[str, Any]] = {}
        self._rotation_timestamps: Dict[str, datetime] = {}

    def get_current_jwt_key(self) -> str:
        """Get the current active JWT key, rotating if necessary."""
        current_time = datetime.utcnow()

        # Check if we need to rotate the key
        if "jwt" not in self._jwt_keys or self._should_rotate_key("jwt", current_time):
            self._rotate_jwt_key(current_time)

        return self._jwt_keys["jwt"]["key"]

    def get_previous_jwt_key(self) -> Optional[str]:
        """Get the previous JWT key for validation during rotation period."""
        if "jwt" in self._jwt_keys and len(self._jwt_keys["jwt"].get("previous_keys", [])) > 0:
            return self._jwt_keys["jwt"]["previous_keys"][-1]
        return None

    def _should_rotate_key(self, key_type: str, current_time: datetime) -> bool:
        """Determine if a key should be rotated."""
        if key_type not in self._rotation_timestamps:
            return True

        last_rotation = self._rotation_timestamps[key_type]
        rotation_interval = timedelta(hours=self.settings.security.jwt_key_rotation_hours)
        return current_time - last_rotation > rotation_interval

    def _rotate_jwt_key(self, current_time: datetime) -> None:
        """Rotate the JWT key and store the previous one."""
        import secrets

        # Generate new key
        new_key = secrets.token_urlsafe(64)  # 512-bit key

        # Store previous key for validation during transition
        if "jwt" in self._jwt_keys:
            previous_key = self._jwt_keys["jwt"]["key"]
            if "previous_keys" not in self._jwt_keys["jwt"]:
                self._jwt_keys["jwt"]["previous_keys"] = []
            self._jwt_keys["jwt"]["previous_keys"].append(previous_key)

            # Keep only last 2 previous keys
            if len(self._jwt_keys["jwt"]["previous_keys"]) > 2:
                self._jwt_keys["jwt"]["previous_keys"].pop(0)

        # Set new key
        self._jwt_keys["jwt"] = {
            "key": new_key,
            "created_at": current_time,
            "previous_keys": self._jwt_keys.get("jwt", {}).get("previous_keys", [])
        }

        self._rotation_timestamps["jwt"] = current_time
        logger.info(f"JWT key rotated at {current_time}")

    def validate_secret_format(self, secret_name: str, secret_value: str) -> bool:
        """Validate the format of a secret."""
        if not secret_value or len(secret_value.strip()) == 0:
            raise ConfigurationError(f"Secret {secret_name} cannot be empty")

        if len(secret_value) < 32:
            raise ConfigurationError(f"Secret {secret_name} must be at least 32 characters long")

        return True


class ConfigurationFactory:
    """Factory for creating and validating application settings."""

    @staticmethod
    def create_settings(
        environment: Optional[str] = None,
        validate_secrets: bool = True
    ) -> Settings:
        """Create and validate settings for the specified environment."""
        try:
            # Get environment from parameter or environment variable
            env = environment or os.getenv("ENVIRONMENT", "dev")

            # Create base settings using lazy loading
            settings = get_settings_instance()

            # Apply environment-specific overrides
            settings = EnvironmentSettings.create_settings_for_environment(env, settings)

            # Validate environment-specific settings
            EnvironmentSettings.validate_environment_settings(settings)

            if validate_secrets:
                ConfigurationFactory._validate_secrets(settings)

            # Initialize secrets manager
            settings._secrets_manager = SecretsManager(settings)

            logger.info(f"Configuration created for environment: {env}")
            return settings

        except Exception as e:
            logger.error(f"Failed to create configuration: {e}")
            raise ConfigurationError(f"Configuration creation failed: {e}") from e

    @staticmethod
    def _validate_secrets(settings: Settings) -> None:
        """Validate all secrets and sensitive configuration."""
        secrets_manager = SecretsManager(settings)

        # Validate JWT secret key
        try:
            secrets_manager.validate_secret_format("JWT_SECRET_KEY", settings.security.jwt_secret_key)
        except ConfigurationError:
            # If JWT secret key is not set, generate a secure one
            import secrets
            settings.security.jwt_secret_key = secrets.token_urlsafe(64)
            logger.warning("JWT_SECRET_KEY not set, generated secure random key")

        # Validate encryption key
        try:
            secrets_manager.validate_secret_format("ENCRYPTION_KEY", settings.security.encryption_key)
        except ConfigurationError:
            raise ConfigurationError(
                "ENCRYPTION_KEY must be set to a base64-encoded 32-byte key. "
                "Generate with: python -c \"import secrets, base64; print(base64.b64encode(secrets.token_bytes(32)).decode())\""
            )

        # Validate Fernet key
        try:
            secrets_manager.validate_secret_format("FERNET_KEY", settings.security.fernet_key)
        except ConfigurationError:
            raise ConfigurationError(
                "FERNET_KEY must be set to a base64-encoded 32-byte key. "
                "Generate with: python -c \"import secrets, base64; print(base64.b64encode(secrets.token_bytes(32)).decode())\""
            )

        # Validate database URL
        if not settings.database.url and not settings.database_url:
            raise ConfigurationError("DATABASE_URL must be set")

        # Validate Redis URL
        if not settings.redis.url and not settings.redis_url:
            raise ConfigurationError("REDIS_URL must be set")

        # Validate Qdrant URL
        if not settings.app.qdrant_url:
            raise ConfigurationError("QDRANT_URL must be set")

        logger.info("All secrets validated successfully")

    @staticmethod
    def get_secrets_manager(settings: Settings) -> SecretsManager:
        """Get the secrets manager instance from settings."""
        if not hasattr(settings, '_secrets_manager'):
            settings._secrets_manager = SecretsManager(settings)
        return settings._secrets_manager


# Global settings instance with caching
@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get cached application settings."""
    return ConfigurationFactory.create_settings()


def validate_settings() -> Settings:
    """Validate and return application settings (legacy compatibility)."""
    return get_settings()


def reload_settings() -> Settings:
    """Force reload of settings (useful for testing or runtime config changes)."""
    get_settings.cache_clear()
    return get_settings()


# Export commonly used components
__all__ = [
    "Settings",
    "ApplicationSettings",
    "SecuritySettings",
    "DatabaseSettings",
    "RedisSettings",
    "SecretsManager",
    "ConfigurationFactory",
    "get_settings",
    "validate_settings",
    "reload_settings",
    "ConfigurationError"
]