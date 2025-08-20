"""Authentication service utilities."""
from __future__ import annotations

import hashlib
from datetime import datetime, timedelta
from typing import Dict

import jwt

from .. import config
from ..exceptions import InvalidCredentialsError, TokenError

settings = config.get_settings()
USERS: Dict[str, str] = {}


def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


async def register_user(email: str, password: str) -> None:
    if len(password) < settings.password_min_length:
        raise InvalidCredentialsError("Password does not meet policy")
    checks = [any(c.islower() for c in password), any(c.isupper() for c in password), any(c.isdigit() for c in password)]
    if not all(checks):
        raise InvalidCredentialsError("Password does not meet policy")
    USERS[email] = _hash(password)


async def authenticate_user(email: str, password: str) -> bool:
    stored = USERS.get(email)
    if not stored or stored != _hash(password):
        raise InvalidCredentialsError("Invalid email or password")
    return True


async def create_access_token(subject: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_ttl_minutes)
    try:
        return jwt.encode({"sub": subject, "exp": expire}, settings.secret_key, algorithm="HS256")
    except jwt.PyJWTError as exc:  # pragma: no cover - library failure
        raise TokenError("Could not create access token") from exc


async def create_refresh_token(subject: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.refresh_token_ttl_minutes)
    try:
        return jwt.encode({"sub": subject, "exp": expire}, settings.secret_key, algorithm="HS256")
    except jwt.PyJWTError as exc:  # pragma: no cover - library failure
        raise TokenError("Could not create refresh token") from exc


async def decode_token(token: str) -> str:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        return payload["sub"]
    except jwt.PyJWTError as exc:
        raise TokenError("Invalid token") from exc
