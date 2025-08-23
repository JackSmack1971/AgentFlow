import os
import pathlib
import sys
import time

import fakeredis.aioredis
import pytest
from httpx import ASGITransport, AsyncClient

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))

os.environ.setdefault("DATABASE_URL", "postgresql://localhost/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("QDRANT_URL", "http://localhost:6333")
os.environ.setdefault("SECRET_KEY", "test")
os.environ.setdefault("OPENAI_API_KEY", "test")

from apps.api.app import config  # noqa: E402
from apps.api.app.core.cache import Cache, get_cache  # noqa: E402
from apps.api.app.exceptions import CacheError  # noqa: E402
from apps.api.app.main import app  # noqa: E402
from apps.api.app.middleware.audit import MiddlewareError  # noqa: E402
from apps.api.app.models.cache import CacheEntry, CachePostResponse  # noqa: E402

config.get_settings.cache_clear()


@pytest.fixture(autouse=True)
def override_cache() -> None:
    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)
    app.dependency_overrides[get_cache] = lambda: Cache(fake)
    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_cached_get_under_100ms() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        await ac.get("/cache/foo")
        start = time.perf_counter()
        resp = await ac.get("/cache/foo")
        duration = (time.perf_counter() - start) * 1000
        assert resp.status_code == 200
        data = CacheEntry(**resp.json())
        assert data.cached is True
        assert duration < 100


@pytest.mark.asyncio
async def test_idempotent_post() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        headers = {"Idempotency-Key": "abc"}
        payload = {"key": "k1", "value": "v1"}
        first = await ac.post("/cache/items", json=payload, headers=headers)
        assert first.status_code == 201
        second = await ac.post("/cache/items", json=payload, headers=headers)
        assert second.status_code == 201
        data = CachePostResponse(**second.json())
        assert data.cached is True


@pytest.mark.asyncio
async def test_cached_get_error_returns_500(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def failing_get(self: Cache, key: str) -> None:
        raise CacheError("boom")

    monkeypatch.setattr(Cache, "get", failing_get)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/cache/foo")
    assert resp.status_code == 500


@pytest.mark.asyncio
async def test_cached_get_validation_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def invalid_get(self: Cache, key: str) -> dict:
        return {"unexpected": "dict"}

    monkeypatch.setattr(Cache, "get", invalid_get)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        with pytest.raises(MiddlewareError):
            await ac.get("/cache/foo")


@pytest.mark.asyncio
async def test_cached_post_error_returns_500(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def failing_set(
        self: Cache, key: str, value: str, ttl: int | None = None
    ) -> None:
        raise CacheError("boom")

    monkeypatch.setattr(Cache, "set", failing_set)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        headers = {"Idempotency-Key": "abc"}
        payload = {"key": "k1", "value": "v1"}
        resp = await ac.post("/cache/items", json=payload, headers=headers)
    assert resp.status_code == 500


@pytest.mark.asyncio
async def test_cached_post_validation_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def invalid_get(self: Cache, key: str) -> dict:
        return {"unexpected": "dict"}

    monkeypatch.setattr(Cache, "get", invalid_get)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        headers = {"Idempotency-Key": "abc"}
        payload = {"key": "k1", "value": "v1"}
        with pytest.raises(MiddlewareError):
            await ac.post("/cache/items", json=payload, headers=headers)
