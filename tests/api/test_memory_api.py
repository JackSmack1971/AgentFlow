import os
import pathlib
import sys
import types

import pytest
from httpx import ASGITransport, AsyncClient

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))

os.environ.setdefault("DATABASE_URL", "postgresql://localhost/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("OPENAI_API_KEY", "test")
os.environ.setdefault("SECRET_KEY", "test")
os.environ.setdefault("QDRANT_URL", "http://localhost:6333")

# Stub pydantic_ai to avoid heavy dependency
mock_ai = types.ModuleType("pydantic_ai")


class DummyAgent:
    def __init__(self, *args: object, **kwargs: object) -> None:
        self.settings = None

    async def run(self, prompt: str):  # pragma: no cover - stub
        class R:
            output_text = ""

        return R()


mock_ai.Agent = DummyAgent
models_mod = types.ModuleType("pydantic_ai.models")


class DummyModelSettings:
    def __init__(self, **kwargs: object) -> None:
        pass


models_mod.ModelSettings = DummyModelSettings
sys.modules["pydantic_ai"] = mock_ai
sys.modules["pydantic_ai.models"] = models_mod

from apps.api.app.dependencies import User, get_current_user
from apps.api.app.main import app
from apps.api.app.routers import memory as memory_router


@pytest.fixture(autouse=True)
def patch_dependencies():
    async def fake_get_current_user() -> User:
        return User(sub="u1", roles=["user"])

    app.dependency_overrides[get_current_user] = fake_get_current_user
    memory_router.memory_service.backend = None
    memory_router.memory_service._items.clear()
    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_and_get_item() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/memory/items", json={"text": "hello"})
        assert resp.status_code == 200
        item_id = resp.json()["id"]
        resp = await ac.get(f"/memory/items/{item_id}")
        assert resp.status_code == 200
        assert resp.json()["text"] == "hello"


@pytest.mark.asyncio
async def test_list_and_search_items() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        await ac.post("/memory/items", json={"text": "alpha", "tags": ["t1"]})
        await ac.post("/memory/items", json={"text": "beta", "tags": ["t2"]})
        resp = await ac.get("/memory/items", params={"tags": ["t1"]})
        assert resp.status_code == 200
        assert len(resp.json()) == 1
        resp = await ac.get("/memory/search", params={"q": "beta"})
        assert resp.status_code == 200
        assert resp.json()[0]["text"] == "beta"


@pytest.mark.asyncio
async def test_update_and_delete_item() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/memory/items", json={"text": "temp"})
        item_id = resp.json()["id"]
        resp = await ac.put(
            f"/memory/items/{item_id}", json={"text": "updated", "tags": ["x"]}
        )
        assert resp.json()["text"] == "updated"
        resp = await ac.delete(f"/memory/items/{item_id}")
        assert resp.status_code == 204
        resp = await ac.get(f"/memory/items/{item_id}")
        assert resp.status_code == 404


@pytest.mark.asyncio
async def test_bulk_import_export() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        items = [{"text": "a"}, {"text": "b"}]
        resp = await ac.post("/memory/items/import", json=items)
        assert resp.status_code == 200
        assert len(resp.json()) == 2
        resp = await ac.post("/memory/items/export")
        assert resp.status_code == 200
        assert len(resp.json()) >= 2
