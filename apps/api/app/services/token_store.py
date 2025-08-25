from __future__ import annotations

from datetime import datetime

import jwt

from .. import config
from ..core.cache import get_cache
from ..exceptions import CacheError, TokenError
from ..utils.encryption import get_encryption_manager

settings = config.get_settings()


def _refresh_key(token: str) -> str:
    return f"refresh:{token}"


def _blacklist_key(token: str) -> str:
    return f"blacklist:{token}"


def _expires_in(token: str) -> int:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise TokenError("Invalid token") from exc
    exp = datetime.fromtimestamp(payload["exp"])
    return max(int((exp - datetime.utcnow()).total_seconds()), 0)


async def store_refresh_token(token: str, subject: str) -> None:
    cache = get_cache()
    ttl = settings.refresh_token_ttl_minutes * 60
    try:
        # Encrypt the subject data before storing
        encryption_manager = get_encryption_manager()
        encrypted_subject = encryption_manager.encrypt(subject)
        await cache.set(_refresh_key(token), encrypted_subject, ttl=ttl)
    except CacheError as exc:  # pragma: no cover - network failure
        raise TokenError("Could not store refresh token") from exc


async def verify_refresh_token(token: str) -> str:
    cache = get_cache()
    try:
        encrypted_subject = await cache.get(_refresh_key(token))
        if not encrypted_subject:
            raise TokenError("Invalid refresh token")

        # Decrypt the subject data
        encryption_manager = get_encryption_manager()
        subject = encryption_manager.decrypt(encrypted_subject)

    except CacheError as exc:  # pragma: no cover - network failure
        raise TokenError("Could not verify refresh token") from exc
    return subject


async def blacklist_refresh_token(token: str) -> None:
    cache = get_cache()
    ttl = _expires_in(token)
    try:
        await cache.set(_blacklist_key(token), "1", ttl=ttl)
    except CacheError as exc:  # pragma: no cover - network failure
        raise TokenError("Could not blacklist token") from exc


async def is_refresh_token_blacklisted(token: str) -> bool:
    cache = get_cache()
    try:
        return bool(await cache.get(_blacklist_key(token)))
    except CacheError as exc:  # pragma: no cover - network failure
        raise TokenError("Could not verify token blacklist") from exc


async def revoke_refresh_token(token: str) -> None:
    cache = get_cache()
    try:
        await cache.client.delete(_refresh_key(token))
        await blacklist_refresh_token(token)
    except Exception as exc:  # pragma: no cover - network failure
        raise TokenError("Could not revoke refresh token") from exc
