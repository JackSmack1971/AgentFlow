import os
import pathlib
import sys

import pytest
from httpx import ASGITransport, AsyncClient

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))
from apps.api.app import config

os.environ.setdefault("DATABASE_URL", "postgresql://localhost/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("OPENAI_API_KEY", "test")
os.environ.setdefault("SECRET_KEY", "test")
os.environ.setdefault("QDRANT_URL", "http://localhost:6333")
config.get_settings.cache_clear()

from apps.api.app.main import app


@pytest.mark.asyncio
async def test_health() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_readiness(monkeypatch) -> None:
    async def ok_postgres(*_: object, **__: object) -> None:
        return None

    async def ok_redis(*_: object, **__: object) -> None:
        return None

    monkeypatch.setattr("apps.api.app.routers.health.check_postgres", ok_postgres)
    monkeypatch.setattr("apps.api.app.routers.health.check_redis", ok_redis)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/readiness")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ready"}
