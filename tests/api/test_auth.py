import os
import pathlib
import sys
import types

import fakeredis.aioredis
import pytest
from httpx import ASGITransport, AsyncClient

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))

os.environ.setdefault("DATABASE_URL", "postgresql://localhost/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("QDRANT_URL", "http://localhost:6333")
os.environ.setdefault("SECRET_KEY", "test")
os.environ.setdefault("OPENAI_API_KEY", "test")

from apps.api.app import config
from apps.api.app.core.cache import Cache
from apps.api.app.main import app
from apps.api.app.services import auth as auth_service
from apps.api.app.services import token_store


# Stub heavy dependencies
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

mock_psycopg = types.ModuleType("psycopg")


class DummyConn:
    async def execute(self, *args: object, **kwargs: object) -> None:
        return None

    async def close(self) -> None:  # pragma: no cover - stub
        return None


class DummyAsyncConnection:
    @staticmethod
    async def connect(dsn: str) -> DummyConn:  # pragma: no cover - stub
        return DummyConn()


mock_psycopg.AsyncConnection = DummyAsyncConnection
sys.modules["psycopg"] = mock_psycopg

config.get_settings.cache_clear()


@pytest.fixture(autouse=True)
def override_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)
    cache = Cache(fake)
    monkeypatch.setattr(token_store, "get_cache", lambda: cache)
    yield


@pytest.mark.asyncio
async def test_register_and_login() -> None:
    auth_service.USERS.clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/auth/register",
            json={"email": "a@b.com", "password": "Password1!"},
        )
        assert resp.status_code == 201
        resp = await ac.post(
            "/auth/login",
            json={"email": "a@b.com", "password": "Password1!"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data and "refresh_token" in data


@pytest.mark.asyncio
async def test_refresh_rotation() -> None:
    auth_service.USERS.clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        await ac.post(
            "/auth/register",
            json={"email": "a@b.com", "password": "Password1!"},
        )
        login = await ac.post(
            "/auth/login",
            json={"email": "a@b.com", "password": "Password1!"},
        )
        token1 = login.json()["refresh_token"]
        first = await ac.post("/auth/refresh", json={"refresh_token": token1})
        assert first.status_code == 200
        token2 = first.json()["refresh_token"]
        replay = await ac.post("/auth/refresh", json={"refresh_token": token1})
        assert replay.status_code == 401
        second = await ac.post("/auth/refresh", json={"refresh_token": token2})
        assert second.status_code == 200


@pytest.mark.asyncio
async def test_logout_blacklists_token() -> None:
    auth_service.USERS.clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        await ac.post(
            "/auth/register",
            json={"email": "a@b.com", "password": "Password1!"},
        )
        login = await ac.post(
            "/auth/login",
            json={"email": "a@b.com", "password": "Password1!"},
        )
        token = login.json()["refresh_token"]
        resp = await ac.post("/auth/logout", json={"refresh_token": token})
        assert resp.status_code == 200
        rejected = await ac.post("/auth/refresh", json={"refresh_token": token})
        assert rejected.status_code == 401


@pytest.mark.asyncio
async def test_refresh_invalid_token() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/auth/refresh", json={"refresh_token": "bad"})
        assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_invalid_credentials() -> None:
    auth_service.USERS.clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        await ac.post(
            "/auth/register",
            json={"email": "a@b.com", "password": "Password1!"},
        )
        resp = await ac.post(
            "/auth/login",
            json={"email": "a@b.com", "password": "WrongPass1!"},
        )
        assert resp.status_code == 401


@pytest.mark.asyncio
async def test_register_password_too_short() -> None:
    auth_service.USERS.clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/auth/register",
            json={"email": "a@b.com", "password": "short"},
        )
        assert resp.status_code == 400


@pytest.mark.asyncio
async def test_register_password_missing_uppercase() -> None:
    auth_service.USERS.clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/auth/register",
            json={"email": "a@b.com", "password": "password1!"},
        )
        assert resp.status_code == 400


@pytest.mark.asyncio
async def test_register_password_banned() -> None:
    auth_service.USERS.clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/auth/register",
            json={"email": "a@b.com", "password": "password"},
        )
        assert resp.status_code == 400


@pytest.mark.asyncio
async def test_password_reset_and_me() -> None:
    auth_service.USERS.clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        await ac.post(
            "/auth/register",
            json={"email": "a@b.com", "password": "Password1!"},
        )
        reset = await ac.post("/auth/reset", json={"email": "a@b.com"})
        assert reset.status_code == 200
        token = reset.json()["reset_token"]
        assert token
        login = await ac.post(
            "/auth/login",
            json={"email": "a@b.com", "password": "Password1!"},
        )
        access = login.json()["access_token"]
        me = await ac.get("/auth/me", headers={"Authorization": f"Bearer {access}"})
        assert me.status_code == 200
        assert me.json()["email"] == "a@b.com"


@pytest.mark.asyncio
async def test_me_unauthorized() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/auth/me")
        assert resp.status_code == 401


@pytest.mark.asyncio
async def test_reset_unknown_user() -> None:
    auth_service.USERS.clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/auth/reset", json={"email": "a@b.com"})
        assert resp.status_code == 404
