import pytest
from sqlalchemy import select

from apps.api.app.db.models import (
    APIKey,
    Agent,
    Membership,
    Organization,
    Role,
    User,
)


@pytest.mark.asyncio
async def test_model_relationships(session) -> None:
    org = Organization(name="Org")
    user = User(email="u@example.com", hashed_password="pwd")
    role = Role(name="admin")
    session.add_all([org, user, role])
    await session.flush()
    session.add(Membership(user_id=user.id, organization_id=org.id, role_id=role.id))
    session.add(Agent(name="Bot", organization_id=org.id))
    session.add(APIKey(user_id=user.id, hashed_key="hk"))
    await session.commit()
    mem = await session.scalar(select(Membership).where(Membership.user_id == user.id))
    assert mem.role_id == role.id
    agent = await session.scalar(select(Agent).where(Agent.organization_id == org.id))
    assert agent.name == "Bot"
