import pytest

from apps.api.app.memory.exceptions import MemoryServiceError
from apps.api.app.services import memory as memory_service_module


def test_missing_openai_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(memory_service_module, "Memory", object())
    monkeypatch.setattr(memory_service_module, "MemoryClient", object())
    with pytest.raises(MemoryServiceError):
        memory_service_module._init_backend()
    monkeypatch.setenv("OPENAI_API_KEY", "test")


def test_invalid_openai_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "bad")

    class DummyMemory:
        @staticmethod
        def from_config(_config: dict) -> None:  # pragma: no cover - simple stub
            raise MemoryServiceError("invalid key")

    monkeypatch.setattr(memory_service_module, "Memory", DummyMemory)
    monkeypatch.setattr(memory_service_module, "MemoryClient", object())
    with pytest.raises(MemoryServiceError):
        memory_service_module._init_backend()
    monkeypatch.setenv("OPENAI_API_KEY", "test")
