"""Authentication service with database-backed user storage."""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Iterable
from datetime import datetime, timedelta
from uuid import uuid4

import jwt
import pyotp
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.settings import get_settings
from ..db.models import User
from ..exceptions import InvalidCredentialsError, OTPError, TokenError
from ..utils.password import hash_password_async, verify_password_async
from . import token_store

is_refresh_token_blacklisted = token_store.is_refresh_token_blacklisted
revoke_refresh_token = token_store.revoke_refresh_token
store_refresh_token = token_store.store_refresh_token
verify_refresh_token = token_store.verify_refresh_token

settings = get_settings()


def _get_jwt_secret() -> str:
    key = settings.jwt_secret_key
    if not key:
        raise TokenError("JWT secret key not configured")
    return key

# Password policy constants
PASSWORD_POLICY_MIN_LENGTH = 8
PASSWORD_POLICY_REQUIRED_CLASSES: dict[str, Callable[[str], bool]] = {
    "lowercase": str.islower,
    "uppercase": str.isupper,
    "digit": str.isdigit,
    "symbol": lambda c: not c.isalnum(),
}
PASSWORD_POLICY_BANNED: Iterable[str] = {"password", "123456", "qwerty"}


def generate_totp_secret() -> str:
    return pyotp.random_base32()


class AuthService:
    """Service for user registration and authentication."""

    def __init__(self, db_session: AsyncSession) -> None:
        self.db = db_session

    async def _get_user(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        result = await asyncio.wait_for(self.db.execute(stmt), timeout=5)
        return result.scalar_one_or_none()

    async def verify_totp(self, email: str, code: str) -> None:
        user = await self._get_user(email)
        if not user or not pyotp.TOTP(user.otp_secret).verify(code):
            raise OTPError("Invalid one-time password")

    async def register_user(self, email: str, password: str) -> str:
        if not email or not password:
            raise InvalidCredentialsError("Email and password required")
        if password.lower() in PASSWORD_POLICY_BANNED:
            raise InvalidCredentialsError("Password is not allowed")
        if len(password) < PASSWORD_POLICY_MIN_LENGTH:
            raise InvalidCredentialsError(
                f"Password must be at least {PASSWORD_POLICY_MIN_LENGTH} characters long"
            )
        missing = [
            name
            for name, check in PASSWORD_POLICY_REQUIRED_CLASSES.items()
            if not any(check(ch) for ch in password)
        ]
        if missing:
            raise InvalidCredentialsError("Password must contain " + ", ".join(missing))
        secret = generate_totp_secret()
        hashed = await hash_password_async(password)
        user = User(email=email, otp_secret=secret, hashed_password=hashed)
        self.db.add(user)
        try:
            await asyncio.wait_for(self.db.commit(), timeout=5)
        except IntegrityError as exc:
            await self.db.rollback()
            raise InvalidCredentialsError("User already exists") from exc
        except Exception as exc:  # noqa: BLE001
            await self.db.rollback()
            raise InvalidCredentialsError("Registration failed") from exc
        return secret

    async def authenticate_user(self, email: str, password: str, otp_code: str) -> bool:
        user = await self._get_user(email)
        if not user or not await verify_password_async(
            password, user.hashed_password
        ):
            raise InvalidCredentialsError("Invalid email or password")
        if not pyotp.TOTP(user.otp_secret).verify(otp_code):
            raise OTPError("Invalid one-time password")
        return True

    async def generate_reset_token(self, email: str) -> str:
        user = await self._get_user(email)
        if not user:
            raise InvalidCredentialsError("User not found")
        return uuid4().hex

    async def get_user_info(self, email: str) -> dict[str, str]:
        user = await self._get_user(email)
        if not user:
            raise InvalidCredentialsError("User not found")
        return {"email": user.email}


async def create_access_token(subject: str) -> str:
    key = _get_jwt_secret()
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_ttl_minutes)
    try:
        payload = {
            "sub": subject,
            "exp": expire,
            "jti": uuid4().hex,
            "aud": "agentflow-api",      # ADD AUDIENCE
            "iss": "agentflow-auth",     # ADD ISSUER
            "iat": datetime.utcnow()     # ADD ISSUED AT
        }
        return jwt.encode(payload, key, algorithm="HS256")
    except jwt.PyJWTError as exc:  # pragma: no cover - library failure
        raise TokenError("Could not create access token") from exc


async def create_refresh_token(subject: str) -> str:
    key = _get_jwt_secret()
    expire = datetime.utcnow() + timedelta(minutes=settings.refresh_token_ttl_minutes)
    try:
        payload = {
            "sub": subject,
            "exp": expire,
            "jti": uuid4().hex,
            "aud": "agentflow-api",      # ADD AUDIENCE
            "iss": "agentflow-auth",     # ADD ISSUER
            "iat": datetime.utcnow()     # ADD ISSUED AT
        }
        return jwt.encode(payload, key, algorithm="HS256")
    except jwt.PyJWTError as exc:  # pragma: no cover - library failure
        raise TokenError("Could not create refresh token") from exc


async def decode_token(token: str) -> str:
    key = _get_jwt_secret()
    try:
        payload = jwt.decode(
            token,
            key,
            algorithms=["HS256"],
            audience="agentflow-api",     # VALIDATE AUDIENCE
            issuer="agentflow-auth"       # VALIDATE ISSUER
        )
        return payload["sub"]
    except jwt.InvalidAudienceError:
        raise TokenError("Invalid token audience")
    except jwt.InvalidIssuerError:
        raise TokenError("Invalid token issuer")
    except jwt.PyJWTError as exc:
        raise TokenError("Invalid token") from exc


__all__ = [
    "AuthService",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "generate_totp_secret",
    "is_refresh_token_blacklisted",
    "revoke_refresh_token",
    "store_refresh_token",
    "verify_refresh_token",
]
