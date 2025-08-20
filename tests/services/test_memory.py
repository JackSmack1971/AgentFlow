import pytest
from apps.api.app.services import memory as mem_service
from apps.api.app.exceptions import MemoryServiceError

class DummyMemory:
    def add(self, *_, **__):
        return {"id": "1"}

    def search(self, *_, **__):
        return [{"id": "1", "text": "hi"}]

@pytest.mark.asyncio
async def test_add_memory(monkeypatch) -> None:
    monkeypatch.setattr(mem_service, "memory", DummyMemory())
    result = await mem_service.add_memory("hello", user_id="u")
    assert result["id"] == "1"

@pytest.mark.asyncio
async def test_add_memory_error(monkeypatch) -> None:
    class Fail:
        def add(self, *_, **__):
            raise RuntimeError("boom")
    monkeypatch.setattr(mem_service, "memory", Fail())
    with pytest.raises(MemoryServiceError):
        await mem_service.add_memory("hi", user_id="u")

@pytest.mark.asyncio
async def test_search_error(monkeypatch) -> None:
    class Fail:
        def search(self, *_, **__):
            raise RuntimeError("boom")
    monkeypatch.setattr(mem_service, "memory", Fail())
    with pytest.raises(MemoryServiceError):
        await mem_service.search_memories("hi")

@pytest.mark.asyncio
async def test_search_validation() -> None:
    with pytest.raises(ValueError):
        await mem_service.search_memories("")
