"""Tests for database utilities."""

from __future__ import annotations

import importlib
from typing import Any

import pytest
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)
from sqlalchemy.ext.asyncio import create_async_engine as sa_create_async_engine

from apps.api.app.exceptions import AgentFlowError


@pytest.mark.asyncio
async def test_get_session_returns_async_session(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """get_session should yield an AsyncSession instance."""

    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    monkeypatch.setenv("SECRET_KEY", "test")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("QDRANT_URL", "http://localhost:6333")
    monkeypatch.setattr(
        "sqlalchemy.ext.asyncio.create_async_engine",
        lambda url, **_: sa_create_async_engine(url),
    )
    db = importlib.reload(importlib.import_module("apps.api.app.database"))

    async for session in db.get_session():
        assert isinstance(session, AsyncSession)


@pytest.mark.asyncio
async def test_get_session_wraps_operational_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """get_session should wrap OperationalError in AgentFlowError."""

    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    monkeypatch.setenv("SECRET_KEY", "test")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("QDRANT_URL", "http://localhost:6333")
    monkeypatch.setattr(
        "sqlalchemy.ext.asyncio.create_async_engine",
        lambda url, **_: sa_create_async_engine(url),
    )
    db = importlib.reload(importlib.import_module("apps.api.app.database"))

    class FaultySession:
        async def __aenter__(self) -> Any:
            raise OperationalError("test", {}, None)

        async def __aexit__(
            self, exc_type, exc, tb
        ) -> None:  # pragma: no cover - cleanup
            return None

    db._Session = lambda: FaultySession()

    with pytest.raises(AgentFlowError):
        async for _ in db.get_session():
            pass


def test_get_pool_status_metrics(monkeypatch: pytest.MonkeyPatch) -> None:
    """get_pool_status should report pool metrics."""

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
            return 0

        def checkedout(self) -> int:  # pragma: no cover - simple accessor
            return 0

        def overflow(self) -> int:  # pragma: no cover - simple accessor
            return 0

        def size(self) -> int:  # pragma: no cover - simple accessor
            return 0

    db._engine.pool = FakePool()
    status = db.get_pool_status()
    assert set(status) == {"checked_in", "checked_out", "overflow", "current_size"}
