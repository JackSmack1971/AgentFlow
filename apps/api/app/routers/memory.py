"""Memory API endpoints."""
from __future__ import annotations

from typing import List, Optional

import asyncio
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import StreamingResponse

from ..dependencies import User, require_roles
from ..memory.exceptions import (
    MemoryNotFoundError,
    MemoryServiceError,
    MemoryStreamError,
    MemoryStreamTimeoutError,
)
from ..memory.models import MemoryEvent, MemoryItem, MemoryItemCreate, MemoryItemUpdate, MemoryScope
from ..memory.service import memory_service

router = APIRouter()


@router.post("/items", response_model=MemoryItem, summary="Create memory item")
async def create_memory_item(
    item: MemoryItemCreate,
    user: User = Depends(require_roles(["user"])),
) -> MemoryItem:
    data = item.model_copy()
    if data.scope == MemoryScope.USER and not data.user_id:
        data.user_id = user.sub
    try:
        return await memory_service.add_item(data)
    except MemoryServiceError as exc:  # pragma: no cover - rare
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/items", response_model=List[MemoryItem], summary="List memory items")
async def list_memory_items(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    scope: Optional[MemoryScope] = None,
    tags: Optional[List[str]] = Query(None),
    user: User = Depends(require_roles(["user"])),
) -> List[MemoryItem]:
    return await memory_service.list_items(offset=offset, limit=limit, scope=scope, tags=tags)


@router.get("/items/{item_id}", response_model=MemoryItem, summary="Get memory item")
async def get_memory_item(
    item_id: str,
    user: User = Depends(require_roles(["user"])),
) -> MemoryItem:
    try:
        return await memory_service.get_item(item_id)
    except MemoryNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/items/{item_id}", response_model=MemoryItem, summary="Update memory item")
async def update_memory_item(
    item_id: str,
    data: MemoryItemUpdate,
    user: User = Depends(require_roles(["user"])),
) -> MemoryItem:
    try:
        return await memory_service.update_item(item_id, data)
    except MemoryNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete memory item")
async def delete_memory_item(
    item_id: str,
    user: User = Depends(require_roles(["user"])),
) -> Response:
    try:
        await memory_service.delete_item(item_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except MemoryNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/items/import", response_model=List[MemoryItem], summary="Bulk import memory items")
async def import_memory_items(
    items: List[MemoryItemCreate],
    user: User = Depends(require_roles(["user"])),
) -> List[MemoryItem]:
    return await memory_service.bulk_import(items)


@router.post("/items/export", response_model=List[MemoryItem], summary="Export memory items")
async def export_memory_items(
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    scope: Optional[MemoryScope] = None,
    tags: Optional[List[str]] = Query(None),
    user: User = Depends(require_roles(["user"])),
) -> List[MemoryItem]:
    return await memory_service.bulk_export(offset=offset, limit=limit, scope=scope, tags=tags)


@router.get("/search", response_model=List[MemoryItem], summary="Search memory items")
async def search_memory_items(
    q: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    scope: Optional[MemoryScope] = None,
    tags: Optional[List[str]] = Query(None),
    user: User = Depends(require_roles(["user"])),
) -> List[MemoryItem]:
    return await memory_service.search_items(q, offset=offset, limit=limit, scope=scope, tags=tags)


@router.get("/stream", summary="Stream memory change events")
async def stream_memory_events(
    user: User = Depends(require_roles(["user"])),
) -> StreamingResponse:
    async def event_generator() -> AsyncGenerator[str, None]:
        queue = memory_service.subscribe()
        retries = 0
        try:
            while True:
                try:
                    event: MemoryEvent = await asyncio.wait_for(queue.get(), timeout=30)
                    retries = 0
                    yield f"data: {event.model_dump_json()}\n\n"
                except asyncio.TimeoutError as exc:
                    retries += 1
                    if retries > 3:
                        raise MemoryStreamTimeoutError("stream timeout") from exc
        except MemoryStreamError:
            yield "event: error\ndata: stream closed\n\n"
        finally:
            memory_service.unsubscribe(queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
