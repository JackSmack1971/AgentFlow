"""Role-based access control utilities."""

from __future__ import annotations

import uuid
from typing import Dict, Set

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import Membership, Role
from ..exceptions import RBACError

PERMISSIONS: Dict[str, Dict[str, Set[str]]] = {
    "admin": {"*": {"*"}},
    "member": {"agents": {"read", "write"}},
    "viewer": {"agents": {"read"}},
}


class PermissionRequest(BaseModel):
    user_id: uuid.UUID
    org_id: uuid.UUID
    resource: str = Field(max_length=50)
    action: str = Field(max_length=50)


async def check_permission(session: AsyncSession, req: PermissionRequest) -> bool:
    """Return True if the user's role allows the action on the resource."""
    try:
        stmt = (
            select(Role.name)
            .join(Membership)
            .where(
                Membership.user_id == req.user_id,
                Membership.organization_id == req.org_id,
            )
        )
        role = await session.scalar(stmt)
        if not role:
            return False
        perms = PERMISSIONS.get(role, {})
        actions = perms.get(req.resource, perms.get("*", set()))
        return req.action in actions or "*" in actions
    except Exception as exc:  # pragma: no cover - unexpected
        raise RBACError("Permission check failed") from exc
