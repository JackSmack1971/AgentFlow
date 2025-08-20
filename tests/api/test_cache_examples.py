import os
import pathlib
import sys
import time
import pytest

pytest.skip("API tests not yet supported", allow_module_level=True)

import fakeredis.aioredis
from httpx import ASGITransport, AsyncClient

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))

os.environ.setdefault("DATABASE_URL", "postgresql://localhost/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("QDRANT_URL", "http://localhost:6333")
os.environ.setdefault("SECRET_KEY", "test")
os.environ.setdefault("OPENAI_API_KEY", "test")

from apps.api.app import config
from apps.api.app.core.cache import Cache, get_cache
from apps.api.app.main import app

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
        assert resp.json()["cached"] is True
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
        assert second.json()["cached"] is True
