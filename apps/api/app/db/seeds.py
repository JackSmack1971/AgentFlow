"""Seed database with initial roles and sample user/org."""

from __future__ import annotations

import hashlib
import os
import secrets
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..exceptions import SeedError
from ..utils.crypto import encrypt
from .models import APIKey, Membership, Organization, Role, User


class SeedData(BaseModel):
    org_name: str = Field(default="Example Org", max_length=200)
    user_email: EmailStr = "user@example.com"
    user_password: str = Field(default="change-me", min_length=8)


async def seed_initial_data(session: AsyncSession) -> None:
    """Create default roles and a sample organization with user."""
    data = SeedData()
    try:
        existing = {r.name for r in (await session.scalars(select(Role))).all()}
        for name in ("admin", "member", "viewer"):
            if name not in existing:
                session.add(Role(name=name))
        await session.flush()

        org = Organization(name=data.org_name)
        hashed = hashlib.sha256(data.user_password.encode()).hexdigest()
        user = User(email=data.user_email, hashed_password=hashed)
        session.add_all([org, user])
        await session.flush()

        admin = await session.scalar(select(Role).where(Role.name == "admin"))
        session.add(Membership(user_id=user.id, organization_id=org.id, role_id=admin.id))

        raw_key = os.getenv("SEED_API_KEY") or secrets.token_hex(16)
        session.add(APIKey(user_id=user.id, hashed_key=encrypt(raw_key)))
        await session.commit()
    except Exception as exc:  # pragma: no cover - unexpected
        await session.rollback()
        raise SeedError("Failed to seed initial data") from exc
