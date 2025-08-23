"""Tests for database session and pool utilities."""

from __future__ import annotations

import importlib

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine as sa_create_async_engine


@pytest.mark.asyncio
async def test_get_session_yields_async_session_and_cleans_up(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """get_session should yield an AsyncSession and close it after use."""

    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    monkeypatch.setenv("SECRET_KEY", "test")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("QDRANT_URL", "http://localhost:6333")
    monkeypatch.setattr(
        "sqlalchemy.ext.asyncio.create_async_engine",
        lambda url, **_: sa_create_async_engine(url),
    )
    db = importlib.reload(importlib.import_module("apps.api.app.database"))

    close_called = False

    async def fake_close(self: AsyncSession) -> None:
        nonlocal close_called
        close_called = True

    monkeypatch.setattr(AsyncSession, "close", fake_close, raising=False)

    async for session in db.get_session():
        assert isinstance(session, AsyncSession)

    assert close_called


def test_get_pool_status_returns_expected_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    """get_pool_status should return pool metrics with integer values."""

    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    monkeypatch.setenv("SECRET_KEY", "test")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("QDRANT_URL", "http://localhost:6333")
    monkeypatch.setattr(
        "sqlalchemy.ext.asyncio.create_async_engine",
        lambda url, **_: sa_create_async_engine(url),
    )
    db = importlib.reload(importlib.import_module("apps.api.app.database"))

    class FakePool:
        def checkedin(self) -> int:  # pragma: no cover - simple accessor
            return 1

        def checkedout(self) -> int:  # pragma: no cover - simple accessor
            return 2

        def overflow(self) -> int:  # pragma: no cover - simple accessor
            return 0

        def size(self) -> int:  # pragma: no cover - simple accessor
            return 3

    db._engine.pool = FakePool()  # type: ignore[attr-defined]
    status = db.get_pool_status()
    expected_keys = {"checked_in", "checked_out", "overflow", "current_size"}
    assert set(status) == expected_keys
    assert all(isinstance(status[key], int) for key in expected_keys)
