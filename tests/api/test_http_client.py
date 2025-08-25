import httpx
import pytest
import respx

from apps.api.app import config
from apps.api.app.deps import http


@pytest.mark.asyncio
@respx.mock
async def test_http_client_retries_and_succeeds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SECRET_KEY", "x")
    monkeypatch.setenv("DATABASE_URL", "postgresql://test")
    monkeypatch.setenv("REDIS_URL", "redis://localhost")
    monkeypatch.setenv("QDRANT_URL", "http://localhost:6333")
    monkeypatch.setenv("HTTP_MAX_RETRIES", "2")
    monkeypatch.setenv("JWT_SECRET_KEY", "test_jwt_secret_key_32_chars_min_length")
    monkeypatch.setenv("ENCRYPTION_KEY", "YmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmI=")
    monkeypatch.setenv("FERNET_KEY", "YWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWE=")
    config.get_settings.cache_clear()
    await http.startup_http_client()
    route = respx.get("https://example.com/")
    route.side_effect = [httpx.ConnectError("boom"), httpx.Response(200)]
    resp = await http.request("GET", "https://example.com/")
    assert resp.status_code == 200
    await http.shutdown_http_client()


@pytest.mark.asyncio
@respx.mock
async def test_circuit_breaker_opens(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SECRET_KEY", "x")
    monkeypatch.setenv("DATABASE_URL", "postgresql://test")
    monkeypatch.setenv("REDIS_URL", "redis://localhost")
    monkeypatch.setenv("QDRANT_URL", "http://localhost:6333")
    monkeypatch.setenv("HTTP_MAX_RETRIES", "1")
    monkeypatch.setenv("HTTP_CB_FAILURE_THRESHOLD", "1")
    monkeypatch.setenv("JWT_SECRET_KEY", "test_jwt_secret_key_32_chars_min_length")
    monkeypatch.setenv("ENCRYPTION_KEY", "YmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmI=")
    monkeypatch.setenv("FERNET_KEY", "YWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWE=")
    config.get_settings.cache_clear()
    await http.startup_http_client()
    respx.get("https://fail.com/").mock(side_effect=httpx.ConnectError("boom"))
    with pytest.raises(http.HttpClientError):
        await http.request("GET", "https://fail.com/")
    with pytest.raises(http.CircuitBreakerError):
        await http.request("GET", "https://fail.com/")
    await http.shutdown_http_client()
