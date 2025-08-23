import os
import pathlib
import sys
import types
from types import SimpleNamespace

import pytest

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))

# Minimal environment configuration
os.environ.setdefault("DATABASE_URL", "postgresql://localhost/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("OPENAI_API_KEY", "test")
os.environ.setdefault("SECRET_KEY", "test")
os.environ.setdefault("QDRANT_URL", "http://localhost:6333")

# Stub pydantic_ai to avoid heavy dependency during tests
mock_ai = types.ModuleType("pydantic_ai")


class DummyAgent:
    def __init__(self, *args: object, **kwargs: object) -> None:
        self.settings = None

    async def run(self, prompt: str) -> object:  # pragma: no cover - stub
        class R:
            output_text = "ok"

        return R()


mock_ai.Agent = DummyAgent
models_mod = types.ModuleType("pydantic_ai.models")


class DummyModelSettings:
    def __init__(self, **kwargs: object) -> None:  # pragma: no cover - stub
        pass


models_mod.ModelSettings = DummyModelSettings
sys.modules["pydantic_ai"] = mock_ai
sys.modules["pydantic_ai.models"] = models_mod

from apps.api.app.exceptions import AgentFlowError
from apps.api.app.services.agents import AgentService
from apps.api.app.services.agents import run_agent as module_run_agent


@pytest.mark.asyncio
async def test_run_agent_success() -> None:
    agent = DummyAgent()
    settings = SimpleNamespace(
        agent_retry_max_attempts=1,
        agent_retry_backoff_seconds=0,
        agent_run_timeout_seconds=1,
    )
    service = AgentService(agent, settings_factory=lambda: settings)
    result = await service.run_agent("hi")
    assert result == "ok"


@pytest.mark.asyncio
async def test_run_agent_invalid_prompt() -> None:
    agent = DummyAgent()
    settings = SimpleNamespace(
        agent_retry_max_attempts=1,
        agent_retry_backoff_seconds=0,
        agent_run_timeout_seconds=1,
    )
    service = AgentService(agent, settings_factory=lambda: settings)
    with pytest.raises(AgentFlowError):
        await service.run_agent("   ")


@pytest.mark.asyncio
async def test_run_agent_failure() -> None:
    class BadAgent(DummyAgent):
        async def run(self, prompt: str) -> object:  # pragma: no cover - stub
            raise RuntimeError("boom")

    settings = SimpleNamespace(
        agent_retry_max_attempts=1,
        agent_retry_backoff_seconds=0,
        agent_run_timeout_seconds=1,
    )
    service = AgentService(BadAgent(), settings_factory=lambda: settings)
    with pytest.raises(AgentFlowError):
        await service.run_agent("hi")


@pytest.mark.asyncio
async def test_module_run_agent(monkeypatch: pytest.MonkeyPatch) -> None:
    class ModuleAgent(DummyAgent):
        async def run(self, prompt: str) -> object:  # pragma: no cover - stub
            class R:
                output_text = "module"

            return R()

    settings = SimpleNamespace(
        agent_retry_max_attempts=1,
        agent_retry_backoff_seconds=0,
        agent_run_timeout_seconds=1,
    )
    monkeypatch.setattr(
        "apps.api.app.services.agents._service",
        AgentService(ModuleAgent(), settings_factory=lambda: settings),
    )
    result = await module_run_agent("ping")
    assert result == "module"
