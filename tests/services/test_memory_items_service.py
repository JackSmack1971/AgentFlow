import os

import pytest

os.environ.setdefault("OPENAI_API_KEY", "test")
os.environ.setdefault("QDRANT_HOST", "localhost")
os.environ.setdefault("QDRANT_PORT", "6333")

from apps.api.app.memory.exceptions import MemoryNotFoundError
from apps.api.app.models.schemas import MemoryItem
from apps.api.app.services.memory_items import ScopedMemoryService


@pytest.fixture
def service() -> ScopedMemoryService:
    return ScopedMemoryService()


@pytest.mark.asyncio
async def test_add_and_get(service: ScopedMemoryService) -> None:
    item = MemoryItem(text="hello", scope="user", user_id="u1")
    stored = await service.add(item)
    fetched = await service.get(stored.id)
    assert fetched.text == "hello"
    assert fetched.user_id == "u1"


@pytest.mark.asyncio
async def test_get_missing_raises(service: ScopedMemoryService) -> None:
    with pytest.raises(MemoryNotFoundError):
        await service.get("missing")


@pytest.mark.asyncio
async def test_search_with_scope_filter(service: ScopedMemoryService) -> None:
    await service.add(MemoryItem(text="hello world", scope="user"))
    await service.add(MemoryItem(text="another", scope="agent", agent_id="a1"))
    results = await service.search("hello", scope="user")
    assert len(results) == 1
    assert results[0].scope == "user"


@pytest.mark.asyncio
async def test_search_requires_query(service: ScopedMemoryService) -> None:
    with pytest.raises(ValueError):
        await service.search("")
