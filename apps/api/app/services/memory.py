"""Memory service layer.

This module provides the memory service used by the API routers. It mirrors the
functionality defined for the memory router and exposes an asynchronous
interface for managing memory items. The implementation wraps the optional
`mem0` backend when available and falls back to in-memory storage for tests.
"""

from __future__ import annotations

import asyncio
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential

from ..memory.exceptions import MemoryNotFoundError, MemoryServiceError
from ..memory.models import (
    MemoryEvent,
    MemoryItem,
    MemoryItemCreate,
    MemoryItemUpdate,
    MemoryScope,
)

try:  # pragma: no cover - optional dependency
    from mem0 import Memory, MemoryClient  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    Memory = MemoryClient = None


logger = logging.getLogger(__name__)


def _init_backend() -> Any | None:
    """Initialize the Mem0 backend with configuration validation."""

    if Memory is None or MemoryClient is None:  # pragma: no cover - mem0 optional
        return None
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        logger.error("OPENAI_API_KEY is required for memory backend")
        raise MemoryServiceError("OPENAI_API_KEY is required for memory backend")
    mem0_mode = os.getenv("MEM0_MODE", "oss")
    try:
        if mem0_mode == "hosted":
            api_key = os.getenv("MEM0_API_KEY")
            if not api_key:
                raise MemoryServiceError("MEM0_API_KEY is required for hosted mode")
            return MemoryClient(api_key=api_key)
        config = {
            "vector_store": {
                "provider": "qdrant",
                "config": {"host": "localhost", "port": 6333},
            },
            "llm": {
                "provider": "openai",
                "config": {"api_key": openai_key, "model": "gpt-4o-mini"},
            },
            "embedder": {
                "provider": "openai",
                "config": {"api_key": openai_key, "model": "text-embedding-3-small"},
            },
            "version": "v1.1",
        }
        return Memory.from_config(config)
    except MemoryServiceError:
        raise
    except Exception:  # noqa: BLE001
        logger.exception("Memory backend initialization failed")
        return None


try:
    _backend = _init_backend()
except MemoryServiceError as exc:
    logger.error("Backend initialization failed: %s", exc)
    raise


async def _with_retry(
    func: Any,
    *args: Any,
    retries: int = 1,
    timeout: float = 5,
    **kwargs: Any,
) -> Any:
    """Execute a blocking function in a thread with retry and timeout."""

    async for attempt in AsyncRetrying(
        stop=stop_after_attempt(retries + 1),
        wait=wait_exponential(multiplier=0.1),
        reraise=True,
    ):
        with attempt:
            return await asyncio.wait_for(
                asyncio.to_thread(func, *args, **kwargs), timeout
            )


class MemoryService:
    """Service managing memory items with TTL and scoping."""

    def __init__(self, backend: Any | None = _backend) -> None:
        self.backend = backend
        self._items: dict[str, MemoryItem] = {}
        self._subscribers: set[asyncio.Queue[MemoryEvent]] = set()

    def _purge(self) -> None:
        now = datetime.now(timezone.utc)
        expired = [
            k for k, v in self._items.items() if v.expires_at and v.expires_at <= now
        ]
        for k in expired:
            self._items.pop(k, None)

    def subscribe(self) -> asyncio.Queue[MemoryEvent]:
        """Register a new event subscriber."""

        queue: asyncio.Queue[MemoryEvent] = asyncio.Queue()
        self._subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[MemoryEvent]) -> None:
        """Remove an event subscriber."""

        self._subscribers.discard(queue)

    async def _publish(self, event: MemoryEvent) -> None:
        """Publish event to all subscribers."""

        for q in self._subscribers:
            await q.put(event)

    def _prepare_metadata(
        self, data: MemoryItemCreate, expires_at: datetime | None
    ) -> dict[str, Any]:
        """Build metadata payload for backend insertion."""

        return {
            **data.metadata,
            "scope": data.scope.value,
            "tags": data.tags,
            "expires_at": expires_at.isoformat() if expires_at else None,
        }

    async def _insert_backend(
        self, data: MemoryItemCreate, meta: dict[str, Any]
    ) -> tuple[str, list[float]]:
        """Insert memory into backend and return new item id and embedding."""

        if not self.backend:
            return str(uuid.uuid4()), []
        try:
            res = await _with_retry(
                self.backend.add,
                data.text,
                user_id=data.user_id,
                agent_id=data.agent_id,
                metadata=meta,
            )
        except Exception as exc:  # noqa: BLE001
            raise MemoryServiceError("Failed to add memory") from exc
        return str(res.get("id", uuid.uuid4())), res.get("embedding", [])

    async def add_item(self, data: MemoryItemCreate) -> MemoryItem:
        self._purge()
        created_at = datetime.now(timezone.utc)
        expires_at = created_at + timedelta(seconds=data.ttl) if data.ttl else None
        meta = self._prepare_metadata(data, expires_at)
        item_id, embedding = await self._insert_backend(data, meta)
        item = MemoryItem(
            id=item_id,
            text=data.text,
            scope=data.scope,
            user_id=data.user_id,
            agent_id=data.agent_id,
            session_id=data.session_id,
            tags=data.tags,
            metadata=data.metadata,
            embedding=embedding,
            created_at=created_at,
            expires_at=expires_at,
            ttl=data.ttl,
        )
        self._items[item_id] = item
        await self._publish(MemoryEvent(action="created", item=item))
        return item

    async def get_item(self, item_id: str) -> MemoryItem:
        self._purge()
        item = self._items.get(item_id)
        if not item:
            raise MemoryNotFoundError(f"item {item_id} not found")
        return item

    async def list_items(
        self,
        *,
        offset: int = 0,
        limit: int = 50,
        scope: MemoryScope | None = None,
        tags: list[str] | None = None,
    ) -> list[MemoryItem]:
        self._purge()
        items = list(self._items.values())
        if scope:
            items = [i for i in items if i.scope == scope]
        if tags:
            items = [i for i in items if set(tags).issubset(set(i.tags))]
        return items[offset : offset + limit]

    async def update_item(self, item_id: str, data: MemoryItemUpdate) -> MemoryItem:
        item = await self.get_item(item_id)
        if data.text is not None:
            item.text = data.text
        if data.tags is not None:
            item.tags = data.tags
        if data.metadata is not None:
            item.metadata = data.metadata
        if data.ttl is not None:
            item.ttl = data.ttl
            item.expires_at = item.created_at + timedelta(seconds=data.ttl)
        self._items[item_id] = item
        await self._publish(MemoryEvent(action="updated", item=item))
        return item

    async def delete_item(self, item_id: str) -> None:
        self._purge()
        if item_id not in self._items:
            raise MemoryNotFoundError(f"item {item_id} not found")
        item = self._items.pop(item_id)
        await self._publish(MemoryEvent(action="deleted", item=item))

    async def search_items(
        self,
        query: str,
        *,
        limit: int = 10,
        offset: int = 0,
        scope: MemoryScope | None = None,
        tags: list[str] | None = None,
    ) -> list[MemoryItem]:
        if not query:
            raise ValueError("query must not be empty")
        self._purge()
        results: list[MemoryItem] = []
        try:
            if self.backend:
                res = await _with_retry(
                    self.backend.search, query, limit=limit + offset
                )
                ids = [r.get("id") for r in res]
                results = [self._items[i] for i in ids if i in self._items]
            else:
                for item in self._items.values():
                    if query.lower() in item.text.lower():
                        results.append(item)
        except Exception as exc:  # noqa: BLE001
            raise MemoryServiceError("Failed to search memories") from exc
        if scope:
            results = [i for i in results if i.scope == scope]
        if tags:
            results = [i for i in results if set(tags).issubset(set(i.tags))]
        return results[offset : offset + limit]

    async def bulk_import(self, items: list[MemoryItemCreate]) -> list[MemoryItem]:
        return await asyncio.gather(*(self.add_item(i) for i in items))

    async def bulk_export(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
        scope: MemoryScope | None = None,
        tags: list[str] | None = None,
    ) -> list[MemoryItem]:
        return await self.list_items(offset=offset, limit=limit, scope=scope, tags=tags)


memory_service = MemoryService()

__all__ = [
    "MemoryService",
    "memory_service",
]
