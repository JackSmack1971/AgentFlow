"""Database connection utilities.

This module provides access to a pooled SQLAlchemy AsyncEngine and session
management helpers for the FastAPI application.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from .config import get_settings
from .exceptions import AgentFlowError, ErrorCode

_settings = get_settings()

_engine: AsyncEngine = create_async_engine(
    _settings.database_url,
    pool_size=getattr(_settings, "db_pool_size", 5),
    max_overflow=getattr(_settings, "db_max_overflow", 10),
    pool_timeout=getattr(_settings, "db_pool_timeout", 30),
    pool_recycle=getattr(_settings, "db_pool_recycle", 1_800),
    pool_pre_ping=True,
)

_Session = async_sessionmaker(_engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an asynchronous database session."""

    try:
        async with _Session() as session:
            yield session
    except OperationalError as exc:  # pragma: no cover - infrastructure
        raise AgentFlowError("Database session error", ErrorCode.DOMAIN_ERROR) from exc


def get_pool_status() -> dict[str, int]:
    """Return current database pool metrics."""

    pool: Any = _engine.pool
    return {
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "current_size": pool.size(),
    }
