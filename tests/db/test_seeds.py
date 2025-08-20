import pytest

from sqlalchemy import select

from apps.api.app.db.models import Organization, Role, User
from apps.api.app.db.seeds import seed_initial_data


@pytest.mark.asyncio
async def test_seed_initial_data(session, monkeypatch) -> None:
    monkeypatch.setenv("SEED_API_KEY", "testkey")
    await seed_initial_data(session)
    roles = await session.scalars(select(Role))
    assert {r.name for r in roles} == {"admin", "member", "viewer"}
    org = await session.scalar(select(Organization))
    user = await session.scalar(select(User))
    assert org.name == "Example Org"
    assert user.email == "user@example.com"
