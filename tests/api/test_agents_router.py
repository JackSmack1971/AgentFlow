import pytest
from httpx import ASGITransport, AsyncClient

from apps.api.app.exceptions import AgentFlowError
from apps.api.app.main import app
from apps.api.app.models.schemas import AgentRunResponse
from apps.api.app.routers import agents as agents_router


@pytest.mark.asyncio
async def test_run_agent_success(monkeypatch) -> None:
    async def fake_run_agent(prompt: str) -> str:
        return "ok"

    monkeypatch.setattr(agents_router, "run_agent", fake_run_agent)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/agents/run", json={"prompt": "hello"})
    assert resp.status_code == 200
    assert resp.json() == {"result": "ok"}
    model = AgentRunResponse(**resp.json())
    assert model.result == "ok"


@pytest.mark.asyncio
async def test_run_agent_failure(monkeypatch) -> None:
    async def fake_run_agent(prompt: str) -> str:
        raise AgentFlowError("boom")

    monkeypatch.setattr(agents_router, "run_agent", fake_run_agent)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/agents/run", json={"prompt": "fail"})
    assert resp.status_code == 500
    assert resp.json()["detail"] == "boom"
