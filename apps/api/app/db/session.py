"""Database session utilities."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from ..config import get_settings
from ..exceptions import AgentFlowError

_engine = create_async_engine(get_settings().database_url, future=True)
_Session = async_sessionmaker(_engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a database session and ensure proper cleanup."""
    try:
        async with _Session() as session:
            yield session
    except Exception as exc:  # pragma: no cover - infrastructure failure
        raise AgentFlowError("Database session error") from exc
