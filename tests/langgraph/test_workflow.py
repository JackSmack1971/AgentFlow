import os
import pathlib
import sys
import types
from typing import Any

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))

os.environ.setdefault("SECRET_KEY", "test")

# Stub external LangGraph dependency
mock_langgraph = types.ModuleType("langgraph_sdk")


class DummyRunner:
    async def run(self, workflow_id: str, inputs: dict[str, Any]) -> dict[str, Any]:
        return {"message": "ok"}


class FailingRunner:
    async def run(self, workflow_id: str, inputs: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError("boom")


mock_langgraph.WorkflowRunner = DummyRunner  # type: ignore[attr-defined]
sys.modules["langgraph_sdk"] = mock_langgraph

from apps.api.app.routers import workflow as workflow_router  # noqa: E402
from apps.api.app.services import workflow as workflow_service  # noqa: E402


def create_app(service: workflow_service.WorkflowService) -> FastAPI:
    app = FastAPI()
    app.dependency_overrides[workflow_router.get_service] = lambda: service
    app.include_router(workflow_router.router, prefix="/workflow")
    return app


@pytest.mark.asyncio
async def test_run_workflow_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(workflow_service, "get_runner", lambda: DummyRunner())
    app = create_app(workflow_service.WorkflowService())
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/workflow/run",
            json={"workflow_id": "wf", "inputs": {"x": 1}},
        )
    assert resp.status_code == 200
    assert resp.json() == {"result": {"message": "ok"}}


@pytest.mark.asyncio
async def test_run_workflow_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(workflow_service, "get_runner", lambda: FailingRunner())
    app = create_app(workflow_service.WorkflowService())
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/workflow/run",
            json={"workflow_id": "wf", "inputs": {}},
        )
    assert resp.status_code == 500
    assert resp.json()["detail"] == "workflow execution failed"
