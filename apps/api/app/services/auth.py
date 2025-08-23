"""Authentication service utilities."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from datetime import datetime, timedelta
from uuid import uuid4

import jwt
import pyotp

from .. import config
from ..exceptions import InvalidCredentialsError, OTPError, TokenError
from ..utils.password import hash_password, verify_password
from . import token_store

is_refresh_token_blacklisted = token_store.is_refresh_token_blacklisted
revoke_refresh_token = token_store.revoke_refresh_token
store_refresh_token = token_store.store_refresh_token
verify_refresh_token = token_store.verify_refresh_token

settings = config.get_settings()
USERS: dict[str, str] = {}
OTP_SECRETS: dict[str, str] = {}

# Password policy constants
PASSWORD_POLICY_MIN_LENGTH = 8
PASSWORD_POLICY_REQUIRED_CLASSES: dict[str, Callable[[str], bool]] = {
    "lowercase": str.islower,
    "uppercase": str.isupper,
    "digit": str.isdigit,
    "symbol": lambda c: not c.isalnum(),
}
PASSWORD_POLICY_BANNED: Iterable[str] = {
    "password",
    "123456",
    "qwerty",
}


def generate_totp_secret() -> str:
    return pyotp.random_base32()


async def verify_totp(email: str, code: str) -> None:
    secret = OTP_SECRETS.get(email)
    if not secret or not pyotp.TOTP(secret).verify(code):
        raise OTPError("Invalid one-time password")


async def register_user(email: str, password: str) -> str:
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

    USERS[email] = hash_password(password)
    secret = generate_totp_secret()
    OTP_SECRETS[email] = secret
    return secret


async def authenticate_user(email: str, password: str, otp_code: str) -> bool:
    stored = USERS.get(email)
    if not stored or not verify_password(password, stored):
        raise InvalidCredentialsError("Invalid email or password")
    await verify_totp(email, otp_code)
    return True


async def create_access_token(subject: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_ttl_minutes)
    try:
        payload = {"sub": subject, "exp": expire, "jti": uuid4().hex}
        return jwt.encode(payload, settings.secret_key, algorithm="HS256")
    except jwt.PyJWTError as exc:  # pragma: no cover - library failure
        raise TokenError("Could not create access token") from exc


async def create_refresh_token(subject: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.refresh_token_ttl_minutes)
    try:
        payload = {"sub": subject, "exp": expire, "jti": uuid4().hex}
        return jwt.encode(payload, settings.secret_key, algorithm="HS256")
    except jwt.PyJWTError as exc:  # pragma: no cover - library failure
        raise TokenError("Could not create refresh token") from exc


async def decode_token(token: str) -> str:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        return payload["sub"]
    except jwt.PyJWTError as exc:
        raise TokenError("Invalid token") from exc


async def generate_reset_token(email: str) -> str:
    if email not in USERS:
        raise InvalidCredentialsError("User not found")
    return uuid4().hex


async def get_user_info(email: str) -> dict[str, str]:
    if email not in USERS:
        raise InvalidCredentialsError("User not found")
    return {"email": email}
