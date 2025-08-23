"""Async Redis cache with retry logic."""

from __future__ import annotations

from typing import Any

from redis.asyncio import Redis
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from ..exceptions import CacheError
from .settings import get_settings


class Cache:
    """Wrapper around Redis with resilience."""

    def __init__(self, client: Redis, default_ttl: int = 60) -> None:
        self.client = client
        self.default_ttl = default_ttl

    @retry(
        retry=retry_if_exception_type(Exception),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=2),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    async def get(self, key: str) -> str | None:
        """Retrieve a value from cache."""

        try:
            return await self.client.get(key)
        except Exception as exc:  # noqa: BLE001
            raise CacheError(f"get failed: {exc}") from exc

    @retry(
        retry=retry_if_exception_type(Exception),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=2),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Store a value in cache."""

        try:
            await self.client.set(key, value, ex=ttl or self.default_ttl)
        except Exception as exc:  # noqa: BLE001
            raise CacheError(f"set failed: {exc}") from exc


_cache: Cache | None = None


def get_cache() -> Cache:
    """Return a singleton cache instance."""

    global _cache
    if _cache is None:
        settings = get_settings()
        client = Redis.from_url(settings.redis_url, decode_responses=True)
        _cache = Cache(client)
    return _cache