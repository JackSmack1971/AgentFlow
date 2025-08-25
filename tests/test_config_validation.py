import pytest

from apps.api.app import config


def test_validate_settings_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.setenv("DATABASE_URL", "postgresql://test")
    monkeypatch.setenv("REDIS_URL", "redis://localhost")
    monkeypatch.setenv("QDRANT_URL", "http://localhost:6333")
    monkeypatch.setenv("JWT_SECRET_KEY", "test_jwt_secret_key_32_chars_min_length")
    monkeypatch.setenv("ENCRYPTION_KEY", "YmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmI=")
    monkeypatch.setenv("FERNET_KEY", "YWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWE=")
    config.get_settings.cache_clear()
    with pytest.raises(RuntimeError):
        config.validate_settings()


def test_validate_settings_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SECRET_KEY", "x")
    monkeypatch.setenv("DATABASE_URL", "postgresql://test")
    monkeypatch.setenv("REDIS_URL", "redis://localhost")
    monkeypatch.setenv("QDRANT_URL", "http://localhost:6333")
    monkeypatch.setenv("JWT_SECRET_KEY", "test_jwt_secret_key_32_chars_min_length")
    monkeypatch.setenv("ENCRYPTION_KEY", "YmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmI=")
    monkeypatch.setenv("FERNET_KEY", "YWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWE=")
    config.get_settings.cache_clear()
    assert config.validate_settings()
