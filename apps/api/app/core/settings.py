"""Application settings loaded from environment variables."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Pydantic settings for core configuration."""

    model_config = SettingsConfigDict(env_file=".env", extra="forbid")

    app_name: str = "AgentFlow API"
    secret_key: str
    openapi_url: str = "/openapi.json"
    database_url: str
    database_pool_size: int = Field(
        default=10, description="Size of the database connection pool."
    )
    database_pool_max_overflow: int = Field(
        default=20, description="Extra connections allowed beyond the pool size."
    )
    database_pool_timeout: float = Field(
        default=30.0,
        description="Seconds to wait for a connection from the pool before timing out.",
    )
    database_pool_recycle: int = Field(
        default=1800, description="Seconds after which connections are recycled."
    )
    redis_url: str
    qdrant_url: str
    r2r_base_url: str = "http://localhost:7272"
    r2r_api_key: str | None = None
    log_level: str = "INFO"
    password_min_length: int = 8
    access_token_ttl_minutes: int = 15
    refresh_token_ttl_minutes: int = 60 * 24
    agent_run_timeout_seconds: int = 30
    agent_retry_max_attempts: int = 3
    agent_retry_backoff_seconds: float = 1.0
    memory_api_timeout: float = 5.0
    memory_api_retries: int = 1
    max_body_size: int = 1024 * 1024
    http_timeout: float = 5.0
    http_max_retries: int = 3
    http_cb_failure_threshold: int = 5
    http_cb_reset_seconds: int = 60

    # Circuit Breaker Configuration
    cb_failure_threshold: int = 3
    cb_recovery_timeout_seconds: float = 10.0

    # Service-specific timeouts for circuit breakers
    service_timeout_mem0: float = 5.0
    service_timeout_qdrant: float = 3.0
    service_timeout_r2r: float = 8.0
    service_timeout_neo4j: float = 5.0

    # Security Configuration
    environment: str = Field(default="dev", description="Environment: dev, staging, or prod")
    security_rate_limit_per_minute: int = Field(default=100, description="Requests per minute per IP")
    security_penetration_attempts_threshold: int = Field(default=5, description="Failed attempts before ban")
    security_ban_duration_minutes: int = Field(default=60, description="Ban duration in minutes")
    security_dev_ip_whitelist: list[str] = Field(
        default=["127.0.0.1", "::1", "192.168.0.0/16"],
        description="IP whitelist for development environment"
    )
    security_log_file: str = Field(default="logs/security.log", description="Security events log file")


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""

    return Settings()  # type: ignore[call-arg]
