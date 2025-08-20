import os
import pathlib
import sys
import pytest

pytest.skip("API tests not yet supported", allow_module_level=True)

from httpx import ASGITransport, AsyncClient

import types

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))

os.environ.setdefault("DATABASE_URL", "postgresql://localhost/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("QDRANT_URL", "http://localhost:6333")
os.environ.setdefault("SECRET_KEY", "test")
os.environ.setdefault("OPENAI_API_KEY", "test")

from apps.api.app import config

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

from apps.api.app.services import auth as auth_service
from apps.api.app.main import app

config.get_settings.cache_clear()


@pytest.mark.asyncio
async def test_register_and_login() -> None:
    auth_service.USERS.clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/auth/register",
            json={"email": "a@b.com", "password": "Password1"},
        )
        assert resp.status_code == 201
        resp = await ac.post(
            "/auth/login",
            json={"email": "a@b.com", "password": "Password1"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data and "refresh_token" in data


@pytest.mark.asyncio
async def test_register_bad_password() -> None:
    auth_service.USERS.clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/auth/register",
            json={"email": "a@b.com", "password": "short"},
        )
        assert resp.status_code == 400


@pytest.mark.asyncio
async def test_login_invalid_credentials() -> None:
    auth_service.USERS.clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        await ac.post(
            "/auth/register",
            json={"email": "a@b.com", "password": "Password1"},
        )
        resp = await ac.post(
            "/auth/login",
            json={"email": "a@b.com", "password": "WrongPass1"},
        )
        assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh() -> None:
    auth_service.USERS.clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        await ac.post(
            "/auth/register",
            json={"email": "a@b.com", "password": "Password1"},
        )
        login = await ac.post(
            "/auth/login",
            json={"email": "a@b.com", "password": "Password1"},
        )
        refresh_token = login.json()["refresh_token"]
        resp = await ac.post("/auth/refresh", json={"refresh_token": refresh_token})
        assert resp.status_code == 200
        data = resp.json()
        assert data["access_token"] and data["refresh_token"]


@pytest.mark.asyncio
async def test_refresh_invalid_token() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/auth/refresh", json={"refresh_token": "bad"})
        assert resp.status_code == 401
