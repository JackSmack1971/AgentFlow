"""Example routes demonstrating caching and idempotent POST."""

import asyncio

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel

from ..core.cache import Cache, get_cache
from ..exceptions import CacheError
from ..models.cache import CacheEntry, CachePostResponse

router = APIRouter()


class Item(BaseModel):
    key: str
    value: str


@router.get("/cache/{key}", response_model=CacheEntry)
async def cached_get(
    key: str, cache: Cache = Depends(get_cache)
) -> CacheEntry:  # noqa: E501
    """Return data using Redis caching."""

    try:
        cached = await cache.get(key)
        if cached is not None:
            return CacheEntry(key=key, value=cached, cached=True)
        await asyncio.sleep(0.2)
        value = f"value-for-{key}"
        await cache.set(key, value)
        return CacheEntry(key=key, value=value, cached=False)
    except CacheError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post(
    "/cache/items",
    status_code=status.HTTP_201_CREATED,
    response_model=CachePostResponse,
)
async def cached_post(
    item: Item,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    cache: Cache = Depends(get_cache),
) -> CachePostResponse:
    """Idempotent item creation using cache."""

    try:
        existing = await cache.get(idempotency_key)
        if existing is not None:
            return CachePostResponse(
                id=idempotency_key,
                value=existing,
                cached=True,
            )
        await cache.set(idempotency_key, item.value)
        return CachePostResponse(
            id=idempotency_key,
            value=item.value,
            cached=False,
        )
    except CacheError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
