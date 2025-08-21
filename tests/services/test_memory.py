import os
from datetime import datetime, timedelta, timezone

import pytest

os.environ.setdefault("OPENAI_API_KEY", "test")

from apps.api.app.memory.exceptions import MemoryNotFoundError, MemoryServiceError
from apps.api.app.memory.models import (
    MemoryItemCreate,
    MemoryItemUpdate,
    MemoryScope,
)
from apps.api.app.services.memory import memory_service as mem_service


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
async def test_add_memory_retry_success(monkeypatch) -> None:
    calls = 0

    class Flaky:
        def add(self, *_, **__):
            nonlocal calls
            calls += 1
            if calls < 2:
                raise RuntimeError("temp")
            return {"id": "1", "embedding": []}

    monkeypatch.setattr(mem_service, "backend", Flaky())
    mem_service._items.clear()
    data = MemoryItemCreate(text="hello", user_id="u")
    result = await mem_service.add_item(data)
    assert result.id == "1"
    assert calls == 2


@pytest.mark.asyncio
async def test_add_memory_error(monkeypatch) -> None:
    calls = 0

    class Fail:
        def add(self, *_, **__):
            nonlocal calls
            calls += 1
            raise RuntimeError("boom")

    monkeypatch.setattr(mem_service, "backend", Fail())
    mem_service._items.clear()
    data = MemoryItemCreate(text="hi", user_id="u")
    with pytest.raises(MemoryServiceError):
        await mem_service.add_item(data)
    assert calls == 2


@pytest.mark.asyncio
async def test_search_error(monkeypatch) -> None:
    calls = 0

    class Fail:
        def search(self, *_, **__):
            nonlocal calls
            calls += 1
            raise RuntimeError("boom")

    monkeypatch.setattr(mem_service, "backend", Fail())
    with pytest.raises(MemoryServiceError):
        await mem_service.search_items("hi")
    assert calls == 2


@pytest.mark.asyncio
async def test_search_validation() -> None:
    with pytest.raises(ValueError):
        await mem_service.search_items("")


@pytest.mark.asyncio
async def test_search_backend_success(monkeypatch) -> None:
    monkeypatch.setattr(mem_service, "backend", DummyBackend())
    mem_service._items.clear()
    await mem_service.add_item(MemoryItemCreate(text="hi", user_id="u"))
    results = await mem_service.search_items("hi")
    assert results and results[0].id == "1"


@pytest.mark.asyncio
async def test_get_list_and_purge(monkeypatch) -> None:
    monkeypatch.setattr(mem_service, "backend", None)
    mem_service._items.clear()
    item = await mem_service.add_item(
        MemoryItemCreate(text="hi", user_id="u", tags=["a"])
    )
    await mem_service.add_item(
        MemoryItemCreate(text="bye", user_id="u", scope=MemoryScope.GLOBAL, tags=["b"])
    )
    fetched = await mem_service.get_item(item.id)
    assert fetched.id == item.id
    scoped = await mem_service.list_items(scope=MemoryScope.GLOBAL)
    assert len(scoped) == 1 and scoped[0].scope is MemoryScope.GLOBAL
    tagged = await mem_service.list_items(tags=["a"])
    assert tagged[0].id == item.id
    mem_service._items[item.id].expires_at = fetched.created_at - timedelta(seconds=1)
    await mem_service.list_items()
    assert item.id not in mem_service._items
    with pytest.raises(MemoryNotFoundError):
        await mem_service.get_item("missing")


@pytest.mark.asyncio
async def test_update_and_delete(monkeypatch) -> None:
    monkeypatch.setattr(mem_service, "backend", None)
    mem_service._items.clear()
    item = await mem_service.add_item(
        MemoryItemCreate(text="old", user_id="u", tags=["t"], metadata={"a": 1}, ttl=10)
    )
    updated = await mem_service.update_item(
        item.id,
        MemoryItemUpdate(text="new", tags=["n"], metadata={"b": 2}, ttl=20),
    )
    assert updated.text == "new"
    assert updated.tags == ["n"]
    assert updated.metadata == {"b": 2}
    assert updated.ttl == 20
    await mem_service.delete_item(item.id)
    assert item.id not in mem_service._items
    with pytest.raises(MemoryNotFoundError):
        await mem_service.delete_item(item.id)


@pytest.mark.asyncio
async def test_search_success_filters(monkeypatch) -> None:
    monkeypatch.setattr(mem_service, "backend", None)
    mem_service._items.clear()
    item = await mem_service.add_item(
        MemoryItemCreate(
            text="hello world", user_id="u", tags=["x"], scope=MemoryScope.USER
        )
    )
    await mem_service.add_item(
        MemoryItemCreate(text="bye", user_id="u", tags=["y"], scope=MemoryScope.GLOBAL)
    )
    res = await mem_service.search_items("hello")
    assert res and res[0].id == item.id
    scoped = await mem_service.search_items("bye", scope=MemoryScope.GLOBAL)
    assert len(scoped) == 1
    tagged = await mem_service.search_items("hello", tags=["x"])
    assert len(tagged) == 1


@pytest.mark.asyncio
async def test_bulk_import_export(monkeypatch) -> None:
    monkeypatch.setattr(mem_service, "backend", None)
    mem_service._items.clear()
    items = [MemoryItemCreate(text=str(i), user_id="u") for i in range(3)]
    created = await mem_service.bulk_import(items)
    assert len(created) == 3
    exported = await mem_service.bulk_export()
    assert len(exported) >= 3


@pytest.mark.asyncio
async def test_prepare_metadata() -> None:
    data = MemoryItemCreate(text="hi", user_id="u", tags=["t"], metadata={"a": 1})
    expires = datetime.now(timezone.utc) + timedelta(seconds=60)
    meta = mem_service._prepare_metadata(data, expires)
    assert meta["scope"] == "user"
    assert meta["tags"] == ["t"]
    assert meta["expires_at"] == expires.isoformat()


@pytest.mark.asyncio
async def test_insert_backend_helpers(monkeypatch) -> None:
    monkeypatch.setattr(mem_service, "backend", None)
    data = MemoryItemCreate(text="hi", user_id="u")
    item_id, embedding = await mem_service._insert_backend(data, {})
    assert item_id and isinstance(embedding, list)


@pytest.mark.asyncio
async def test_insert_backend_error(monkeypatch) -> None:
    class Fail:
        def add(self, *_, **__):
            raise RuntimeError("boom")

    monkeypatch.setattr(mem_service, "backend", Fail())
    data = MemoryItemCreate(text="hi", user_id="u")
    with pytest.raises(MemoryServiceError):
        await mem_service._insert_backend(data, {})
