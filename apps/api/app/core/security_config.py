"""Unified Security Configuration Management System.

This module provides centralized configuration management for all security components:
- Rate limiting settings
- Encryption configuration
- Security monitoring parameters
- JWT security settings
- OTP configuration
- Integration with existing settings
"""

import os
from typing import Dict, List, Optional, Any
from functools import lru_cache

from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings

from .settings import Settings


class EncryptionConfig(BaseModel):
    """Encryption service configuration."""

    key_env_var: str = Field(default="FERNET_KEY", description="Environment variable for encryption key")
    auto_generate_key: bool = Field(default=True, description="Auto-generate key if not provided")
    key_rotation_days: int = Field(default=90, description="Days before key rotation reminder")
    algorithm: str = Field(default="AES256", description="Encryption algorithm")

    def get_key(self) -> str:
        """Get encryption key from environment or generate one."""
        key = os.getenv(self.key_env_var)
        if key:
            return key

        if self.auto_generate_key:
            # In production, this should be set via environment variable
            # This is a fallback for development
            return "dev-key-change-in-production"

        raise ValueError(f"Encryption key not found in {self.key_env_var}")


class RateLimitConfig(BaseModel):
    """Rate limiting configuration."""

    requests_per_minute: int = Field(default=100, description="Requests per minute per IP")
    burst_limit: int = Field(default=10, description="Burst capacity")
    window_seconds: int = Field(default=60, description="Rate limit window")
    strategy: str = Field(default="sliding_window", description="Rate limiting strategy")
    redis_prefix: str = Field(default="rate_limit", description="Redis key prefix")

    # Advanced settings
    enable_redis: bool = Field(default=True, description="Use Redis for distributed rate limiting")
    local_cache_ttl: int = Field(default=30, description="Local cache TTL in seconds")
    whitelist_ips: List[str] = Field(default_factory=list, description="IP addresses to whitelist")


class SecurityMonitoringConfig(BaseModel):
    """Security monitoring configuration."""

    enable_real_time_alerts: bool = Field(default=True, description="Enable real-time alerts")
    enable_anomaly_detection: bool = Field(default=False, description="Enable anomaly detection")
    metrics_retention_days: int = Field(default=30, description="Metrics retention period")
    redis_prefix: str = Field(default="security", description="Redis key prefix")

    # Alert thresholds
    alert_thresholds: Dict[str, int] = Field(
        default_factory=lambda: {
            "rate_limit_exceeded": 5,
            "unauthorized_access": 3,
            "suspicious_login": 3,
            "sql_injection": 1,
            "xss_attempt": 3,
            "brute_force": 5,
            "dos_attack": 10
        },
        description="Alert thresholds for different event types"
    )

    # Notification settings
    enable_email_alerts: bool = Field(default=False, description="Enable email alerts")
    enable_slack_alerts: bool = Field(default=False, description="Enable Slack alerts")
    alert_email_recipients: List[str] = Field(default_factory=list, description="Email recipients for alerts")


class JWTConfig(BaseModel):
    """JWT security configuration."""

    secret_key_env_var: str = Field(default="SECRET_KEY", description="Environment variable for JWT secret")
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_ttl_minutes: int = Field(default=15, description="Access token TTL")
    refresh_token_ttl_minutes: int = Field(default=1440, description="Refresh token TTL")
    audience: str = Field(default="agentflow-api", description="JWT audience")
    issuer: str = Field(default="agentflow-auth", description="JWT issuer")

    # Security features
    enable_jti: bool = Field(default=True, description="Enable JWT ID")
    enable_session_tracking: bool = Field(default=True, description="Enable session tracking")
    max_tokens_per_user: int = Field(default=10, description="Maximum active tokens per user")
    token_rotation_grace_period: int = Field(default=30, description="Token rotation grace period in seconds")


class OTPConfig(BaseModel):
    """OTP configuration."""

    length: int = Field(default=6, description="OTP length")
    ttl_minutes: int = Field(default=10, description="OTP time-to-live")
    algorithm: str = Field(default="TOTP", description="OTP algorithm")
    issuer: str = Field(default="AgentFlow", description="OTP issuer name")

    # Security settings
    max_attempts: int = Field(default=3, description="Maximum verification attempts")
    lockout_minutes: int = Field(default=15, description="Lockout period after max attempts")
    enable_backup_codes: bool = Field(default=True, description="Enable backup codes")


class SecurityConfig(BaseModel):
    """Unified security configuration."""

    # Core settings
    environment: str = Field(default="development", description="Environment: development, staging, production")
    enable_security: bool = Field(default=True, description="Enable security features")

    # Component configurations
    encryption: EncryptionConfig = Field(default_factory=EncryptionConfig)
    rate_limiting: RateLimitConfig = Field(default_factory=RateLimitConfig)
    monitoring: SecurityMonitoringConfig = Field(default_factory=SecurityMonitoringConfig)
    jwt: JWTConfig = Field(default_factory=JWTConfig)
    otp: OTPConfig = Field(default_factory=OTPConfig)

    # Global settings
    log_level: str = Field(default="INFO", description="Security logging level")
    log_file: str = Field(default="logs/security.log", description="Security log file")
    enable_file_logging: bool = Field(default=True, description="Enable file logging")
    enable_console_logging: bool = Field(default=True, description="Enable console logging")

    # Performance settings
    redis_connection_pool_size: int = Field(default=10, description="Redis connection pool size")
    cache_ttl: int = Field(default=300, description="Security cache TTL")

    @validator('environment')
    def validate_environment(cls, v):
        """Validate environment setting."""
        valid_envs = ['development', 'staging', 'production', 'test']
        if v not in valid_envs:
            raise ValueError(f'Environment must be one of: {valid_envs}')
        return v

    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"

    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"

    def get_rate_limit_for_ip(self, ip: str) -> Dict[str, Any]:
        """Get rate limiting configuration for specific IP."""
        if ip in self.rate_limiting.whitelist_ips:
            return {"requests_per_minute": 1000, "burst_limit": 100}

        return {
            "requests_per_minute": self.rate_limiting.requests_per_minute,
            "burst_limit": self.rate_limiting.burst_limit,
            "window_seconds": self.rate_limiting.window_seconds
        }


class SecurityConfigManager:
    """Manager for security configuration with integration capabilities."""

    def __init__(self, base_settings: Settings):
        """Initialize with existing settings."""
        self.base_settings = base_settings
        self._config = None

    @property
    def config(self) -> SecurityConfig:
        """Get unified security configuration."""
        if self._config is None:
            self._config = self._build_config()
        return self._config

    def _build_config(self) -> SecurityConfig:
        """Build unified configuration from existing settings."""
        return SecurityConfig(
            environment=self.base_settings.environment,
            enable_security=getattr(self.base_settings, 'enable_security', True),

            # Rate limiting
            rate_limiting=RateLimitConfig(
                requests_per_minute=self.base_settings.security_rate_limit_per_minute,
                burst_limit=10,
                window_seconds=60,
                whitelist_ips=self.base_settings.security_dev_ip_whitelist if self.base_settings.environment == "dev" else []
            ),

            # JWT settings
            jwt=JWTConfig(
                access_token_ttl_minutes=self.base_settings.access_token_ttl_minutes,
                refresh_token_ttl_minutes=self.base_settings.refresh_token_ttl_minutes
            ),

            # Monitoring
            monitoring=SecurityMonitoringConfig(
                enable_real_time_alerts=True,
                alert_thresholds={
                    "rate_limit_exceeded": 5,
                    "unauthorized_access": 3,
                    "suspicious_login": 3,
                    "sql_injection": 1,
                    "xss_attempt": 3,
                    "brute_force": self.base_settings.security_penetration_attempts_threshold,
                    "dos_attack": 10
                }
            ),

            # Global settings
            log_level=self.base_settings.log_level,
            log_file=self.base_settings.security_log_file
        )

    def update_config(self, **kwargs) -> None:
        """Update configuration dynamically."""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
            else:
                # Handle nested updates
                if '.' in key:
                    parent, child = key.split('.', 1)
                    if hasattr(self.config, parent):
                        parent_obj = getattr(self.config, parent)
                        if hasattr(parent_obj, child):
                            setattr(parent_obj, child, value)

    def get_service_config(self, service_name: str) -> Dict[str, Any]:
        """Get configuration for specific service."""
        config_map = {
            'rate_limiting': self.config.rate_limiting,
            'encryption': self.config.encryption,
            'monitoring': self.config.monitoring,
            'jwt': self.config.jwt,
            'otp': self.config.otp
        }

        if service_name in config_map:
            return config_map[service_name].dict()

        raise ValueError(f"Unknown service: {service_name}")

    def validate_config(self) -> List[str]:
        """Validate security configuration."""
        issues = []

        # Check encryption key
        try:
            self.config.encryption.get_key()
        except ValueError as e:
            issues.append(str(e))

        # Check environment-specific settings
        if self.config.is_production():
            if self.config.encryption.auto_generate_key:
                issues.append("Auto-generated encryption keys should not be used in production")

            if not self.config.monitoring.enable_real_time_alerts:
                issues.append("Real-time alerts should be enabled in production")

        # Check rate limiting settings
        if self.config.rate_limiting.requests_per_minute < 1:
            issues.append("Rate limit must be at least 1 request per minute")

        # Check JWT settings
        if self.config.jwt.access_token_ttl_minutes > 60:
            issues.append("Access token TTL should not exceed 60 minutes for security")

        return issues

    def get_health_status(self) -> Dict[str, Any]:
        """Get security configuration health status."""
        issues = self.validate_config()

        return {
            "status": "healthy" if not issues else "warning" if len(issues) < 3 else "critical",
            "issues": issues,
            "services": {
                "encryption": {"configured": True, "key_available": self._check_encryption_key()},
                "rate_limiting": {"configured": True, "redis_available": self.config.rate_limiting.enable_redis},
                "monitoring": {"configured": True, "alerts_enabled": self.config.monitoring.enable_real_time_alerts},
                "jwt": {"configured": True, "secure_algorithm": self.config.jwt.algorithm in ["HS256", "RS256"]},
                "otp": {"configured": True, "secure_length": self.config.otp.length >= 6}
            }
        }

    def _check_encryption_key(self) -> bool:
        """Check if encryption key is available."""
        try:
            self.config.encryption.get_key()
            return True
        except ValueError:
            return False


# Global configuration manager instance
_security_config_manager: Optional[SecurityConfigManager] = None


def get_security_config_manager(settings: Settings) -> SecurityConfigManager:
    """Get global security configuration manager."""
    global _security_config_manager
    if _security_config_manager is None:
        _security_config_manager = SecurityConfigManager(settings)
    return _security_config_manager


def get_security_config() -> SecurityConfig:
    """Get unified security configuration."""
    from .settings import get_settings
    manager = get_security_config_manager(get_settings())
    return manager.config


__all__ = [
    "SecurityConfig",
    "SecurityConfigManager",
    "get_security_config_manager",
    "get_security_config",
    "EncryptionConfig",
    "RateLimitConfig",
    "SecurityMonitoringConfig",
    "JWTConfig",
    "OTPConfig"
]