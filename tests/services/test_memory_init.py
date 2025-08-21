import importlib
import sys
import types
import pytest

from apps.api.app.services import memory as memory_service_module
from apps.api.app.memory.exceptions import MemoryServiceError


@pytest.mark.asyncio
async def test_hosted_mode_initialization_success(monkeypatch) -> None:
    monkeypatch.setenv("MEM0_MODE", "hosted")
    monkeypatch.setenv("MEM0_API_KEY", "testkey")

    class DummyMemoryClient:
        def __init__(self, api_key: str) -> None:  # pragma: no cover - simple stub
            self.api_key = api_key
    dummy_mem0 = types.SimpleNamespace(Memory=object(), MemoryClient=DummyMemoryClient)
    monkeypatch.setitem(sys.modules, "mem0", dummy_mem0)
    importlib.reload(memory_service_module)
    assert isinstance(memory_service_module._backend, DummyMemoryClient)

    monkeypatch.delenv("MEM0_MODE", raising=False)
    monkeypatch.delenv("MEM0_API_KEY", raising=False)
    monkeypatch.delitem(sys.modules, "mem0", raising=False)
    importlib.reload(memory_service_module)


@pytest.mark.asyncio
async def test_hosted_mode_initialization_missing_key(monkeypatch) -> None:
    monkeypatch.setenv("MEM0_MODE", "hosted")
    monkeypatch.delenv("MEM0_API_KEY", raising=False)

    class DummyMemoryClient:
        def __init__(self, api_key: str) -> None:  # pragma: no cover - simple stub
            self.api_key = api_key

    dummy_mem0 = types.SimpleNamespace(Memory=object(), MemoryClient=DummyMemoryClient)
    monkeypatch.setitem(sys.modules, "mem0", dummy_mem0)
    with pytest.raises(MemoryServiceError):
        importlib.reload(memory_service_module)

    monkeypatch.delenv("MEM0_MODE", raising=False)
    monkeypatch.delitem(sys.modules, "mem0", raising=False)
    importlib.reload(memory_service_module)
