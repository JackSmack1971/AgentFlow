import os
from types import SimpleNamespace

import pytest

os.environ.setdefault("OPENAI_API_KEY", "test")
os.environ.setdefault("SECRET_KEY", "test_secret_key_32_chars_min_length")
os.environ.setdefault("DATABASE_URL", "postgresql://localhost/test")
os.environ.setdefault("REDIS_URL", "redis://localhost")
os.environ.setdefault("QDRANT_URL", "http://localhost:6333")
os.environ.setdefault("JWT_SECRET_KEY", "test_jwt_secret_key_32_chars_min_length")
os.environ.setdefault("ENCRYPTION_KEY", "YmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmI=")
os.environ.setdefault("FERNET_KEY", "YWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWE=")

from apps.api.app.config import get_settings  # noqa: E402
from apps.api.app.exceptions import AgentFlowError  # noqa: E402
from apps.api.app.services import agents as agent_service  # noqa: E402


@pytest.mark.asyncio
async def test_run_agent_retries_success(monkeypatch) -> None:
    calls = {"n": 0}

    async def flaky_run(prompt: str):
        calls["n"] += 1
        if calls["n"] < 3:
            raise RuntimeError("temp")
        return SimpleNamespace(output_text="ok")

    monkeypatch.setattr(agent_service.agent, "run", flaky_run)
    monkeypatch.setenv("AGENT_RETRY_MAX_ATTEMPTS", "3")
    monkeypatch.setenv("AGENT_RETRY_BACKOFF_SECONDS", "0")
    get_settings.cache_clear()

    result = await agent_service.run_agent("hi")
    assert result == "ok"
    assert calls["n"] == 3


@pytest.mark.asyncio
async def test_run_agent_retry_exhaust(monkeypatch) -> None:
    async def always_fail(prompt: str):
        raise RuntimeError("boom")

    monkeypatch.setattr(agent_service.agent, "run", always_fail)
    monkeypatch.setenv("AGENT_RETRY_MAX_ATTEMPTS", "2")
    monkeypatch.setenv("AGENT_RETRY_BACKOFF_SECONDS", "0")
    get_settings.cache_clear()

    with pytest.raises(AgentFlowError):
        await agent_service.run_agent("hi")


@pytest.mark.asyncio
async def test_run_agent_invalid_prompt() -> None:
    with pytest.raises(AgentFlowError):
        await agent_service.run_agent("   ")
