"""Agent orchestration service."""

from __future__ import annotations

import asyncio
from typing import Callable

from pydantic_ai import Agent
from pydantic_ai.models import ModelSettings
from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential

from ..config import get_settings
from ..exceptions import AgentFlowError


class AgentService:
    """Service wrapper around a pydantic-ai Agent with retry logic."""

    def __init__(
        self, agent: Agent, settings_factory: Callable[[], object] = get_settings
    ) -> None:
        self.agent = agent
        self._settings_factory = settings_factory

    async def run_agent(self, prompt: str) -> str:
        settings = self._settings_factory()
        if not prompt or not prompt.strip():
            raise AgentFlowError("Prompt must be a non-empty string")
        try:
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(settings.agent_retry_max_attempts),
                wait=wait_exponential(multiplier=settings.agent_retry_backoff_seconds),
                reraise=True,
            ):
                with attempt:
                    async with asyncio.timeout(settings.agent_run_timeout_seconds):
                        result = await self.agent.run(prompt)
                        return result.output_text
        except Exception as exc:  # noqa: BLE001
            raise AgentFlowError("Agent execution failed") from exc


agent = Agent(
    "openai:gpt-4o",
    system_prompt="You are AgentFlow. Be concise, cite sources when available.",
)
agent.settings = ModelSettings(temperature=0.1, max_tokens=500)

_service = AgentService(agent)


async def run_agent(prompt: str) -> str:
    """Compatibility wrapper for existing imports."""

    return await _service.run_agent(prompt)


__all__ = ["AgentService", "agent", "run_agent"]
