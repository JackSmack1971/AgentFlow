"""Authentication service utilities."""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta
from typing import Callable, Dict, Iterable
from uuid import uuid4

import jwt

from .. import config
from ..core.cache import get_cache
from ..exceptions import CacheError, InvalidCredentialsError, TokenError

settings = config.get_settings()
USERS: Dict[str, str] = {}

# Password policy constants
PASSWORD_POLICY_MIN_LENGTH = 8
PASSWORD_POLICY_REQUIRED_CLASSES: Dict[str, Callable[[str], bool]] = {
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


def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


async def register_user(email: str, password: str) -> None:
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

    USERS[email] = _hash(password)


async def authenticate_user(email: str, password: str) -> bool:
    stored = USERS.get(email)
    if not stored or stored != _hash(password):
        raise InvalidCredentialsError("Invalid email or password")
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


def _refresh_key(token: str) -> str:
    return f"refresh:{token}"


async def store_refresh_token(token: str, subject: str) -> None:
    cache = get_cache()
    ttl = settings.refresh_token_ttl_minutes * 60
    try:
        await cache.set(_refresh_key(token), subject, ttl=ttl)
    except CacheError as exc:  # pragma: no cover - network failure
        raise TokenError("Could not store refresh token") from exc


async def verify_refresh_token(token: str) -> str:
    cache = get_cache()
    try:
        subject = await cache.get(_refresh_key(token))
    except CacheError as exc:  # pragma: no cover - network failure
        raise TokenError("Could not verify refresh token") from exc
    if not subject:
        raise TokenError("Invalid refresh token")
    return subject


async def revoke_refresh_token(token: str) -> None:
    cache = get_cache()
    try:
        await cache.client.delete(_refresh_key(token))
    except Exception as exc:  # pragma: no cover - network failure
        raise TokenError("Could not revoke refresh token") from exc
