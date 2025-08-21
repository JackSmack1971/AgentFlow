import os
from unittest.mock import Mock

import pytest

os.environ.setdefault("SECRET_KEY", "test")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("QDRANT_URL", "http://localhost:6333")
os.environ.setdefault("OPENAI_API_KEY", "test")

from apps.api.app.memory.exceptions import MemoryServiceError
from apps.api.app.memory.models import MemoryItemCreate, MemoryScope
from apps.api.app.services.memory import MemoryService


@pytest.fixture
def fake_backend() -> Mock:
    backend = Mock()
    backend.add.return_value = {"id": "1", "embedding": [0.1, 0.2]}
    backend.search.return_value = [{"id": "1"}]
    backend.update.return_value = None
    backend.delete.return_value = None
    return backend


@pytest.fixture
def service(fake_backend: Mock) -> MemoryService:
    return MemoryService(backend=fake_backend)


@pytest.mark.asyncio
async def test_add_and_search(service: MemoryService, fake_backend: Mock) -> None:
    item = await service.add_item(
        MemoryItemCreate(text="hello", scope=MemoryScope.GLOBAL, ttl=None)
    )
    assert item.id == "1"
    results = await service.search_items("hello")
    assert results and results[0].id == "1"
    fake_backend.add.assert_called_once()
    fake_backend.search.assert_called_once()


@pytest.mark.asyncio
async def test_search_requires_query(service: MemoryService) -> None:
    with pytest.raises(ValueError):
        await service.search_items("")


@pytest.mark.asyncio
async def test_backend_error_raises_service_error(fake_backend: Mock) -> None:
    fake_backend.add.side_effect = Exception("boom")
    service = MemoryService(backend=fake_backend)
    with pytest.raises(MemoryServiceError):
        await service.add_item(
            MemoryItemCreate(text="fail", scope=MemoryScope.GLOBAL, ttl=None)
        )
