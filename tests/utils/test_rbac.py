import pytest

from apps.api.app.db.models import Membership, Organization, Role, User
from apps.api.app.utils.rbac import PermissionRequest, check_permission


@pytest.mark.asyncio
async def test_check_permission(session) -> None:
    org = Organization(name="Org")
    user = User(email="u@example.com", hashed_password="pwd")
    role = Role(name="viewer")
    session.add_all([org, user, role])
    await session.flush()
    session.add(Membership(user_id=user.id, organization_id=org.id, role_id=role.id))
    await session.commit()
    allowed = await check_permission(
        session,
        PermissionRequest(user_id=user.id, org_id=org.id, resource="agents", action="read"),
    )
    denied = await check_permission(
        session,
        PermissionRequest(user_id=user.id, org_id=org.id, resource="agents", action="write"),
    )
    assert allowed is True
    assert denied is False
