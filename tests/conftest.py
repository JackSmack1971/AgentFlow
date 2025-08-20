import pytest_asyncio
import pathlib
import sys
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from apps.api.app.db.base import Base
from apps.api.app.exceptions import AgentFlowError


@pytest_asyncio.fixture
async def session() -> AsyncSession:
    """Provide a transactional in-memory database session for tests."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        Session = async_sessionmaker(engine, expire_on_commit=False)
        async with Session() as session:
            yield session
    except Exception as exc:  # pragma: no cover - test setup failure
        raise AgentFlowError("Test DB setup failed") from exc
    finally:
        await engine.dispose()
