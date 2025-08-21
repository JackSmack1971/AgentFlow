"""LangGraph workflow service.

This module provides a thin wrapper around the LangGraph runner with
timeout and retry logic. It validates basic inputs and converts runtime
errors into :class:`WorkflowExecutionError` exceptions for upstream
handlers.
"""

from __future__ import annotations

import asyncio
from typing import Any, Protocol

from ..exceptions import WorkflowExecutionError


class RunnerProtocol(Protocol):
    """Protocol describing the minimal LangGraph runner interface."""

    async def run(self, workflow_id: str, inputs: dict[str, Any]) -> dict[str, Any]:
        """Execute a workflow and return its result."""


def get_runner() -> RunnerProtocol:  # pragma: no cover - external dependency
    """Return the default LangGraph runner instance."""
    from langgraph_sdk import WorkflowRunner  # type: ignore[import-not-found]

    return WorkflowRunner()


class WorkflowService:
    """Service for executing LangGraph workflows."""

    def __init__(self, runner: RunnerProtocol | None = None) -> None:
        self._runner = runner or get_runner()

    async def execute(self, workflow_id: str, inputs: dict[str, Any]) -> dict[str, Any]:
        """Run a workflow with retries and timeout handling."""
        if not workflow_id:
            raise ValueError("workflow_id must not be empty")

        for attempt in range(3):
            try:
                return await asyncio.wait_for(
                    self._runner.run(workflow_id, inputs), timeout=5.0
                )
            except Exception as exc:  # pragma: no cover - exercised in tests
                if attempt == 2:
                    raise WorkflowExecutionError("workflow execution failed") from exc
                await asyncio.sleep(0.1)

        raise WorkflowExecutionError("workflow execution failed")


__all__ = ["WorkflowService", "get_runner", "RunnerProtocol"]
