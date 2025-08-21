from __future__ import annotations

import asyncio
import os
import uuid
from typing import Any, Dict, List, Optional

from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential

from ..models.schemas import MemoryItem
from ..memory.exceptions import MemoryNotFoundError, MemoryServiceError

try:  # pragma: no cover - optional dependency
    from mem0 import Memory, MemoryClient  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    Memory = MemoryClient = None  # type: ignore


async def _run_with_retry(
    func,
    *args,
    retries: int = 2,
    timeout: float = 5,
    **kwargs,
):
    """Execute blocking function in a thread with retries and timeout."""

    async for attempt in AsyncRetrying(
        stop=stop_after_attempt(retries + 1),
        wait=wait_exponential(multiplier=0.1),
        reraise=True,
    ):
        with attempt:
            return await asyncio.wait_for(
                asyncio.to_thread(func, *args, **kwargs), timeout
            )


def _init_backend() -> Optional[Any]:
    """Initialise Mem0 backend if available."""

    if Memory is None or MemoryClient is None:
        return None
    mode = os.getenv("MEM0_MODE", "oss")
    if mode == "hosted":
        api_key = os.getenv("MEM0_API_KEY")
        if not api_key:
            raise MemoryServiceError("MEM0_API_KEY is required for hosted mode")
        try:
            return MemoryClient(api_key=api_key)
        except Exception as exc:  # noqa: BLE001
            raise MemoryServiceError("Failed to init Mem0 client") from exc
    try:
        return Memory.from_config(
            {
                "vector_store": {
                    "provider": "qdrant",
                    "config": {
                        "host": os.getenv("QDRANT_HOST", "localhost"),
                        "port": int(os.getenv("QDRANT_PORT", "6333")),
                    },
                },
                "llm": {
                    "provider": "openai",
                    "config": {
                        "api_key": os.getenv("OPENAI_API_KEY", ""),
                        "model": "gpt-4o-mini",
                    },
                },
                "embedder": {
                    "provider": "openai",
                    "config": {
                        "api_key": os.getenv("OPENAI_API_KEY", ""),
                        "model": "text-embedding-3-small",
                    },
                },
                "version": "v1.1",
            }
        )
    except Exception:  # pragma: no cover
        return None


class ScopedMemoryService:
    """Manage MemoryItem instances with multi-level scoping."""

    def __init__(self, backend: Optional[Any] = None) -> None:
        self.backend = backend or _init_backend()
        self._items: Dict[str, MemoryItem] = {}

    async def add(self, item: MemoryItem) -> MemoryItem:
        """Store a memory item and return the stored instance."""

        meta = {
            "scope": item.scope,
            "user_id": item.user_id,
            "agent_id": item.agent_id,
            "run_id": item.run_id,
            "metadata": item.metadata or {},
        }
        try:
            if self.backend:
                res = await _run_with_retry(
                    self.backend.add,
                    item.text,
                    user_id=item.user_id,
                    agent_id=item.agent_id,
                    metadata=meta,
                )
                item_id = str(res.get("id", uuid.uuid4()))
            else:
                item_id = str(uuid.uuid4())
        except Exception as exc:  # noqa: BLE001
            raise MemoryServiceError("Failed to add memory") from exc
        stored = item.model_copy(update={"id": item_id})
        self._items[item_id] = stored
        return stored

    async def get(self, item_id: str) -> MemoryItem:
        """Retrieve a memory item by id."""

        item = self._items.get(item_id)
        if not item:
            raise MemoryNotFoundError(f"memory {item_id} not found")
        return item

    async def search(
        self,
        query: str,
        *,
        scope: Optional[str] = None,
        limit: int = 10,
    ) -> List[MemoryItem]:
        """Search memories by text content."""

        if not query.strip():
            raise ValueError("query must not be empty")
        try:
            if self.backend:
                res = await _run_with_retry(
                    self.backend.search, query, limit=limit
                )
                ids = [r.get("id") for r in res]
                results = [self._items[i] for i in ids if i in self._items]
            else:
                results = [
                    m for m in self._items.values() if query.lower() in m.text.lower()
                ]
        except Exception as exc:  # noqa: BLE001
            raise MemoryServiceError("Failed to search memories") from exc
        if scope:
            results = [m for m in results if m.scope == scope]
        return results[:limit]


memory_manager = ScopedMemoryService()

__all__ = ["ScopedMemoryService", "memory_manager"]
