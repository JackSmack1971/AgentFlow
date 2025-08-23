"""Tests for the legacy session module."""

from __future__ import annotations

import importlib

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine as sa_create_async_engine


@pytest.mark.asyncio
async def test_session_reexports_database_get_session(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """get_session should be re-exported from the database module."""

    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    monkeypatch.setenv("SECRET_KEY", "test")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("QDRANT_URL", "http://localhost:6333")
    monkeypatch.setattr(
        "sqlalchemy.ext.asyncio.create_async_engine",
        lambda url, **_: sa_create_async_engine(url),
    )

    database_mod = importlib.reload(importlib.import_module("apps.api.app.database"))
    session_mod = importlib.reload(importlib.import_module("apps.api.app.db.session"))

    assert session_mod.get_session is database_mod.get_session

    async for session in session_mod.get_session():
        assert isinstance(session, AsyncSession)
