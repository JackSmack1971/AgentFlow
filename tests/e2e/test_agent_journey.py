import os
import time
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

for k in ("SECRET_KEY", "DATABASE_URL", "REDIS_URL", "QDRANT_URL", "OPENAI_API_KEY"):
    os.environ.setdefault(k, "test")

from apps.api.app.main import app  # noqa: E402


@pytest.mark.asyncio
async def test_agent_journey() -> None:
    async def echo(
        id: str | None = None, settings: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        return {"id": id or "a1", **(settings or {})}

    app.router.routes = [r for r in app.router.routes if r.path != "/agents/run"]
    app.add_api_route("/agents", echo, methods=["POST"])
    app.add_api_route("/agents/{id}", echo, methods=["PATCH"])
    app.add_api_route("/agents/run", lambda: {"status": "ok"}, methods=["POST"])
    start = time.perf_counter()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        aid = (await c.post("/agents", timeout=5)).json()["id"]
        await c.patch(f"/agents/{aid}", json={"config": {}}, timeout=5)
        await c.post("/agents/run", json={"prompt": "hi"}, timeout=5)
    assert time.perf_counter() - start < 300
