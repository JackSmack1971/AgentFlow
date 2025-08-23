"""Tests for database pool settings environment overrides and defaults."""

import pytest

from apps.api.app import config


@pytest.fixture(autouse=True)
def baseline_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Provide required base environment variables for settings."""
    monkeypatch.setenv("SECRET_KEY", "test")
    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/test")
    monkeypatch.setenv("REDIS_URL", "redis://localhost")
    monkeypatch.setenv("QDRANT_URL", "http://localhost:6333")


@pytest.mark.parametrize(
    "env_name, attr, expected",
    [
        ("DATABASE_POOL_SIZE", "database_pool_size", 10),
        ("DATABASE_POOL_MAX_OVERFLOW", "database_pool_max_overflow", 20),
        ("DATABASE_POOL_TIMEOUT", "database_pool_timeout", 30.0),
        ("DATABASE_POOL_RECYCLE", "database_pool_recycle", 1800),
    ],
)
def test_database_pool_defaults(
    monkeypatch: pytest.MonkeyPatch, env_name: str, attr: str, expected: int | float
) -> None:
    """Should use default when env var is unset."""
    monkeypatch.delenv(env_name, raising=False)
    config.get_settings.cache_clear()
    settings = config.get_settings()
    assert getattr(settings, attr) == expected


@pytest.mark.parametrize(
    "env_name, value, attr, expected",
    [
        ("DATABASE_POOL_SIZE", "15", "database_pool_size", 15),
        ("DATABASE_POOL_MAX_OVERFLOW", "25", "database_pool_max_overflow", 25),
        ("DATABASE_POOL_TIMEOUT", "40", "database_pool_timeout", 40.0),
        ("DATABASE_POOL_RECYCLE", "3600", "database_pool_recycle", 3600),
    ],
)
def test_database_pool_env_override(
    monkeypatch: pytest.MonkeyPatch,
    env_name: str,
    value: str,
    attr: str,
    expected: int | float,
) -> None:
    """Should read env var values when provided."""
    monkeypatch.setenv(env_name, value)
    config.get_settings.cache_clear()
    settings = config.get_settings()
    assert getattr(settings, attr) == expected
