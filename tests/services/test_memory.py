import pytest

from apps.api.app.memory.service import memory_service as mem_service
from apps.api.app.memory.exceptions import MemoryServiceError
from apps.api.app.memory.models import MemoryItemCreate

class DummyBackend:
    def add(self, *_, **__):
        return {"id": "1", "embedding": []}

    def search(self, *_, **__):
        return [{"id": "1", "text": "hi"}]

@pytest.mark.asyncio
async def test_add_memory(monkeypatch) -> None:
    monkeypatch.setattr(mem_service, "backend", DummyBackend())
    mem_service._items.clear()
    data = MemoryItemCreate(text="hello", user_id="u")
    result = await mem_service.add_item(data)
    assert result.id == "1"

@pytest.mark.asyncio
async def test_add_memory_error(monkeypatch) -> None:
    class Fail:
        def add(self, *_, **__):
            raise RuntimeError("boom")

    monkeypatch.setattr(mem_service, "backend", Fail())
    mem_service._items.clear()
    data = MemoryItemCreate(text="hi", user_id="u")
    with pytest.raises(MemoryServiceError):
        await mem_service.add_item(data)

@pytest.mark.asyncio
async def test_search_error(monkeypatch) -> None:
    class Fail:
        def search(self, *_, **__):
            raise RuntimeError("boom")

    monkeypatch.setattr(mem_service, "backend", Fail())
    with pytest.raises(MemoryServiceError):
        await mem_service.search_items("hi")

@pytest.mark.asyncio
async def test_search_validation() -> None:
    with pytest.raises(ValueError):
        await mem_service.search_items("")
