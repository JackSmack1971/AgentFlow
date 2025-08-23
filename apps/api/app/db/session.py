"""Database session compatibility layer."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from ..database import _engine as _engine_instance
from ..database import _Session as _session_factory
from ..database import get_session

engine: AsyncEngine = _engine_instance
async_session_factory: async_sessionmaker[AsyncSession] = _session_factory

__all__ = ["engine", "async_session_factory", "get_session"]
