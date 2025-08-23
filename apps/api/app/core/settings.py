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


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""

    return Settings()  # type: ignore[call-arg]
