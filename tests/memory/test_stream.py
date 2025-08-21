import asyncio
import os

import pytest

os.environ.setdefault("SECRET_KEY", "test")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("QDRANT_URL", "http://localhost:6333")
os.environ.setdefault("OPENAI_API_KEY", "test")

from apps.api.app.memory.models import MemoryItemCreate, MemoryScope
from apps.api.app.services.memory import memory_service


@pytest.mark.asyncio
async def test_stream_emits_events() -> None:
    queue = memory_service.subscribe()
    try:
        await memory_service.add_item(
            MemoryItemCreate(text="hello", scope=MemoryScope.GLOBAL)
        )
        event = await asyncio.wait_for(queue.get(), timeout=1)
        assert event.action == "created"
        assert event.item.text == "hello"
    finally:
        memory_service.unsubscribe(queue)

