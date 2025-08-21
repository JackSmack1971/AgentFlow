"""Integration tests for the AG2 service.

These tests verify that user input is sanitized before it is sent to the AG2
coordinator and that errors from the coordinator are wrapped in the service's
custom exception. The actual AG2 service is optional; tests are skipped if the
module is not yet implemented.
"""

from __future__ import annotations

import importlib
from typing import Any

import pytest

spec = importlib.util.find_spec("apps.api.app.services.ag2")
if spec is None:  # pragma: no cover - module not implemented yet
    pytest.skip("AG2 service not implemented", allow_module_level=True)

ag2 = importlib.import_module("apps.api.app.services.ag2")


class DummyCoordinator:
    """Simple stand-in for the AG2 coordinator used in tests."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def dispatch(self, prompt: str, *, timeout: float = 5.0) -> dict[str, Any]:
        """Record calls and optionally raise to simulate coordinator failures."""
        self.calls.append({"prompt": prompt, "timeout": timeout})
        if "fail" in prompt:
            raise RuntimeError("coordinator error")
        return {"response": "ok"}


@pytest.mark.asyncio
async def test_input_sanitization(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure potentially unsafe input is sanitized before dispatch."""
    coordinator = DummyCoordinator()
    monkeypatch.setattr(ag2, "coordinator", coordinator)

    unsafe_prompt = "<script>alert('xss')</script>"
    await ag2.handle_prompt(unsafe_prompt)

    sent = coordinator.calls[0]["prompt"]
    assert "<" not in sent and ">" not in sent
    assert "alert('xss')" in sent


@pytest.mark.asyncio
async def test_coordinator_error_handling(monkeypatch: pytest.MonkeyPatch) -> None:
    """Errors from the coordinator should raise AG2ServiceError."""
    coordinator = DummyCoordinator()
    monkeypatch.setattr(ag2, "coordinator", coordinator)

    with pytest.raises(ag2.AG2ServiceError):
        await ag2.handle_prompt("fail please")
