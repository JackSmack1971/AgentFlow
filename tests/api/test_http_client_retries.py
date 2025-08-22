import httpx
import pytest
import respx

from apps.api.app import config
from apps.api.app.deps import http


@pytest.mark.asyncio
@respx.mock
async def test_http_client_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SECRET_KEY", "x")
    monkeypatch.setenv("DATABASE_URL", "postgresql://test")
    monkeypatch.setenv("REDIS_URL", "redis://localhost")
    monkeypatch.setenv("QDRANT_URL", "http://localhost:6333")
    monkeypatch.setenv("HTTP_MAX_RETRIES", "3")
    config.get_settings.cache_clear()
    await http.startup_http_client()

    req = httpx.Request("GET", "https://api.example.com/")
    responses: list[httpx.Response | Exception] = [
        httpx.HTTPStatusError("rate", request=req, response=httpx.Response(429)),
        httpx.HTTPStatusError("server", request=req, response=httpx.Response(500)),
        httpx.Response(200),
    ]
    route = respx.get("https://api.example.com/").mock(side_effect=responses)

    response = await http.request("GET", "https://api.example.com/")
    assert response.status_code == 200
    assert route.call_count == 3

    await http.shutdown_http_client()
