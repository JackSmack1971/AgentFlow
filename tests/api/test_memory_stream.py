import asyncio
from datetime import datetime, timezone

import pytest
from httpx import ASGITransport, AsyncClient

from apps.api.app.main import app
from apps.api.app.memory.exceptions import MemoryNotFoundError
from apps.api.app.memory.models import MemoryEvent, MemoryItem, MemoryScope
from apps.api.app.routers import memory as memory_router


@pytest.fixture(autouse=True)
def reset_service() -> None:
    memory_router.memory_service.backend = None
    memory_router.memory_service._items.clear()
    yield


@pytest.mark.asyncio
async def test_stream_memory_events(monkeypatch: pytest.MonkeyPatch) -> None:
    """Stream emits a memory event via server-sent events."""

    class OneShotQueue(asyncio.Queue[MemoryEvent]):
        def __init__(self) -> None:
            super().__init__()
            self._used = False

        async def get(self) -> MemoryEvent:
            if self._used:
                raise asyncio.CancelledError
            self._used = True
            return await super().get()

    queue = OneShotQueue()
    monkeypatch.setattr(memory_router.memory_service, "subscribe", lambda: queue)
    monkeypatch.setattr(memory_router.memory_service, "unsubscribe", lambda q: None)
    item = MemoryItem(
        id="1",
        text="hello",
        scope=MemoryScope.USER,
        user_id="u1",
        tags=[],
        metadata={},
        embedding=[],
        created_at=datetime.now(timezone.utc),
    )
    event = MemoryEvent(action="created", item=item)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:

        async def send_event() -> None:
            await asyncio.sleep(0.1)
            await queue.put(event)

        sender = asyncio.create_task(send_event())
        async with ac.stream("GET", "/memory/stream") as resp:
            assert resp.status_code == 200
            assert resp.headers["content-type"].startswith("text/event-stream")
            line = await resp.aiter_lines().__anext__()
            assert line == f"data: {event.model_dump_json()}"
            await resp.aclose()
        await sender


@pytest.mark.asyncio
async def test_update_item_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """Update returns 404 when memory item is missing."""

    async def fake_update(*args: object, **kwargs: object) -> None:
        raise MemoryNotFoundError("missing")

    monkeypatch.setattr(memory_router.memory_service, "update_item", fake_update)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.put("/memory/items/404", json={"text": "x"})
        assert resp.status_code == 404
        assert resp.json()["detail"] == "missing"


@pytest.mark.asyncio
async def test_delete_item_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """Delete returns 404 when memory item is missing."""

    async def fake_delete(*args: object, **kwargs: object) -> None:
        raise MemoryNotFoundError("missing")

    monkeypatch.setattr(memory_router.memory_service, "delete_item", fake_delete)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.delete("/memory/items/404")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "missing"
