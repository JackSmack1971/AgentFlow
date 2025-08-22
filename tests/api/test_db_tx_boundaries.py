import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.db.models import Organization


class ServiceError(Exception):
    """Raised when the service fails."""


async def failing_service(session: AsyncSession) -> None:
    async with session.begin():
        session.add(Organization(name="Org"))
        raise ServiceError("boom")


@pytest.mark.asyncio
async def test_db_tx_boundaries(session: AsyncSession) -> None:
    with pytest.raises(ServiceError):
        await failing_service(session)
    count = await session.scalar(select(func.count()).select_from(Organization))
    assert count == 0
