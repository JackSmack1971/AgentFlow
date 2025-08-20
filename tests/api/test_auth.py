import os
import pathlib
import sys
import types
import uuid

import fakeredis.aioredis
import pytest
from httpx import ASGITransport, AsyncClient, Response

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))

os.environ.setdefault("DATABASE_URL", "postgresql://localhost/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("QDRANT_URL", "http://localhost:6333")
os.environ.setdefault("SECRET_KEY", "test")
os.environ.setdefault("OPENAI_API_KEY", "test")

import pyotp

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


def assert_correlation_id(resp: Response) -> None:
    assert "X-Correlation-ID" in resp.headers
    uuid.UUID(resp.headers["X-Correlation-ID"])


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
        assert_correlation_id(resp)
        assert resp.status_code == 201
        secret = resp.json()["otp_secret"]
        code = pyotp.TOTP(secret).now()
        resp = await ac.post(
            "/auth/login",
            json={"email": "a@b.com", "password": "Password1!", "otp_code": code},
        )
        assert_correlation_id(resp)
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data and "refresh_token" in data


@pytest.mark.asyncio
async def test_refresh_rotation() -> None:
    auth_service.USERS.clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        reg = await ac.post(
            "/auth/register",
            json={"email": "a@b.com", "password": "Password1!"},
        )
        assert_correlation_id(reg)
        secret = reg.json()["otp_secret"]
        code = pyotp.TOTP(secret).now()
        login = await ac.post(
            "/auth/login",
            json={"email": "a@b.com", "password": "Password1!", "otp_code": code},
        )
        assert_correlation_id(login)
        token1 = login.json()["refresh_token"]
        first = await ac.post("/auth/refresh", json={"refresh_token": token1})
        assert_correlation_id(first)
        assert first.status_code == 200
        token2 = first.json()["refresh_token"]
        replay = await ac.post("/auth/refresh", json={"refresh_token": token1})
        assert_correlation_id(replay)
        assert replay.status_code == 401
        second = await ac.post("/auth/refresh", json={"refresh_token": token2})
        assert_correlation_id(second)
        assert second.status_code == 200


@pytest.mark.asyncio
async def test_logout_blacklists_token() -> None:
    auth_service.USERS.clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        reg = await ac.post(
            "/auth/register",
            json={"email": "a@b.com", "password": "Password1!"},
        )
        assert_correlation_id(reg)
        secret = reg.json()["otp_secret"]
        code = pyotp.TOTP(secret).now()
        login = await ac.post(
            "/auth/login",
            json={"email": "a@b.com", "password": "Password1!", "otp_code": code},
        )
        assert_correlation_id(login)
        token = login.json()["refresh_token"]
        resp = await ac.post("/auth/logout", json={"refresh_token": token})
        assert_correlation_id(resp)
        assert resp.status_code == 200
        rejected = await ac.post("/auth/refresh", json={"refresh_token": token})
        assert_correlation_id(rejected)
        assert rejected.status_code == 401


@pytest.mark.asyncio
async def test_refresh_invalid_token() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/auth/refresh", json={"refresh_token": "bad"})
        assert_correlation_id(resp)
        assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_invalid_credentials() -> None:
    auth_service.USERS.clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        reg = await ac.post(
            "/auth/register",
            json={"email": "a@b.com", "password": "Password1!"},
        )
        assert_correlation_id(reg)
        secret = reg.json()["otp_secret"]
        code = pyotp.TOTP(secret).now()
        resp = await ac.post(
            "/auth/login",
            json={"email": "a@b.com", "password": "WrongPass1!", "otp_code": code},
        )
        assert_correlation_id(resp)
        assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_invalid_otp() -> None:
    auth_service.USERS.clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        reg = await ac.post(
            "/auth/register",
            json={"email": "a@b.com", "password": "Password1!"},
        )
        assert_correlation_id(reg)
        wrong = "000000"
        resp = await ac.post(
            "/auth/login",
            json={"email": "a@b.com", "password": "Password1!", "otp_code": wrong},
        )
        assert_correlation_id(resp)
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
        assert_correlation_id(resp)
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
        assert_correlation_id(resp)
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
        assert_correlation_id(resp)
        assert resp.status_code == 400


@pytest.mark.asyncio
async def test_password_reset_and_me() -> None:
    auth_service.USERS.clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        reg = await ac.post(
            "/auth/register",
            json={"email": "a@b.com", "password": "Password1!"},
        )
        assert_correlation_id(reg)
        secret = reg.json()["otp_secret"]
        reset = await ac.post("/auth/reset", json={"email": "a@b.com"})
        assert_correlation_id(reset)
        assert reset.status_code == 200
        token = reset.json()["reset_token"]
        assert token
        code = pyotp.TOTP(secret).now()
        login = await ac.post(
            "/auth/login",
            json={"email": "a@b.com", "password": "Password1!", "otp_code": code},
        )
        assert_correlation_id(login)
        access = login.json()["access_token"]
        me = await ac.get("/auth/me", headers={"Authorization": f"Bearer {access}"})
        assert_correlation_id(me)
        assert me.status_code == 200
        assert me.json()["email"] == "a@b.com"


@pytest.mark.asyncio
async def test_me_unauthorized() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/auth/me")
        assert_correlation_id(resp)
        assert resp.status_code == 401


@pytest.mark.asyncio
async def test_reset_unknown_user() -> None:
    auth_service.USERS.clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/auth/reset", json={"email": "a@b.com"})
        assert_correlation_id(resp)
        assert resp.status_code == 404
