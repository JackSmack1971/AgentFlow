import os

import pyotp
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from apps.api.app.db.models import User
from apps.api.app.exceptions import InvalidCredentialsError
from apps.api.app.services.auth import AuthService

os.environ.setdefault("SECRET_KEY", "test")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("QDRANT_URL", "http://localhost:6333")


@pytest.mark.asyncio
async def test_register_and_authenticate_user(session: AsyncSession) -> None:
    service = AuthService(session)
    email = "test@example.com"
    password = "StrongPass1!"

    secret = await service.register_user(email, password)
    otp_code = pyotp.TOTP(secret).now()

    assert await service.authenticate_user(email, password, otp_code)

    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one()
    assert user.hashed_password != password

    Session = async_sessionmaker(session.bind, expire_on_commit=False)
    async with Session() as new_session:
        new_service = AuthService(new_session)
        code = pyotp.TOTP(secret).now()
        assert await new_service.authenticate_user(email, password, code)


@pytest.mark.asyncio
async def test_authenticate_user_invalid_password(session: AsyncSession) -> None:
    service = AuthService(session)
    email = "test2@example.com"
    password = "StrongPass1!"

    secret = await service.register_user(email, password)
    otp_code = pyotp.TOTP(secret).now()

    with pytest.raises(InvalidCredentialsError):
        await service.authenticate_user(email, "WrongPass1!", otp_code)
