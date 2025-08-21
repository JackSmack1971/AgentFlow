import os
import pathlib
import sys
import types

import pytest
from httpx import ASGITransport, AsyncClient

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))

os.environ.setdefault("DATABASE_URL", "postgresql://localhost/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("OPENAI_API_KEY", "test")
os.environ.setdefault("SECRET_KEY", "test")
os.environ.setdefault("QDRANT_URL", "http://localhost:6333")

from apps.api.app import config
from apps.api.app.exceptions import HealthCheckError

config.get_settings.cache_clear()
mock_ai = types.ModuleType("pydantic_ai")


class DummyAgent:
    def __init__(self, *args: object, **kwargs: object) -> None:
        self.settings = None

    async def run(self, prompt: str):  # pragma: no cover - stub
        class R:
            output_text = ""

        return R()


class DummyModelSettings:
    def __init__(self, **kwargs: object) -> None:
        pass


mock_ai.Agent = DummyAgent
models_mod = types.ModuleType("pydantic_ai.models")
models_mod.ModelSettings = DummyModelSettings
sys.modules["pydantic_ai"] = mock_ai
sys.modules["pydantic_ai.models"] = models_mod


class DummyConn:
    async def execute(self, *args: object, **kwargs: object) -> None:
        return None

    async def close(self) -> None:  # pragma: no cover - stub
        return None


class DummyAsyncConnection:
    @staticmethod
    async def connect(dsn: str) -> DummyConn:  # pragma: no cover - stub
        return DummyConn()


mock_psycopg = types.ModuleType("psycopg")
mock_psycopg.AsyncConnection = DummyAsyncConnection
sys.modules["psycopg"] = mock_psycopg

from apps.api.app.main import app  # noqa: E402


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


@pytest.mark.asyncio
async def test_readiness_unavailable(monkeypatch) -> None:
    async def fail_postgres(*_: object, **__: object) -> None:
        raise HealthCheckError("postgres", "down")

    monkeypatch.setattr(
        "apps.api.app.routers.health.check_postgres",
        fail_postgres,
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/readiness")
    assert resp.status_code == 503
    assert resp.json() == {"detail": "postgres unavailable"}
