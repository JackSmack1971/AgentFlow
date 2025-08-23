import os
import pyotp
import pytest

os.environ.setdefault("SECRET_KEY", "test")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("QDRANT_URL", "http://localhost:6333")

from apps.api.app.exceptions import InvalidCredentialsError
from apps.api.app.services import auth


@pytest.mark.asyncio
async def test_register_and_authenticate_user():
    auth.USERS.clear()
    auth.OTP_SECRETS.clear()
    email = "test@example.com"
    password = "StrongPass1!"

    secret = await auth.register_user(email, password)
    otp_code = pyotp.TOTP(secret).now()

    assert await auth.authenticate_user(email, password, otp_code)
    assert auth.USERS[email] != password


@pytest.mark.asyncio
async def test_authenticate_user_invalid_password():
    auth.USERS.clear()
    auth.OTP_SECRETS.clear()
    email = "test2@example.com"
    password = "StrongPass1!"

    secret = await auth.register_user(email, password)
    otp_code = pyotp.TOTP(secret).now()

    with pytest.raises(InvalidCredentialsError):
        await auth.authenticate_user(email, "WrongPass1!", otp_code)
