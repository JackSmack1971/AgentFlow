"""Example routes demonstrating caching and idempotent POST."""

import asyncio
from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel

from ..core.cache import Cache, get_cache
from ..exceptions import CacheError

router = APIRouter()


class Item(BaseModel):
    key: str
    value: str


@router.get("/cache/{key}")
async def cached_get(key: str, cache: Cache = Depends(get_cache)) -> dict:
    """Return data using Redis caching."""

    try:
        cached = await cache.get(key)
        if cached is not None:
            return {"key": key, "value": cached, "cached": True}
        await asyncio.sleep(0.2)
        value = f"value-for-{key}"
        await cache.set(key, value)
        return {"key": key, "value": value, "cached": False}
    except CacheError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/cache/items", status_code=status.HTTP_201_CREATED)
async def cached_post(
    item: Item,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    cache: Cache = Depends(get_cache),
) -> dict:
    """Idempotent item creation using cache."""

    try:
        existing = await cache.get(idempotency_key)
        if existing is not None:
            return {"id": idempotency_key, "value": existing, "cached": True}
        await cache.set(idempotency_key, item.value)
        return {"id": idempotency_key, "value": item.value, "cached": False}
    except CacheError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
