import json
import uuid

from fastapi import FastAPI
from fastapi.testclient import TestClient
from loguru import logger

from apps.api.app.middleware.audit import AuditMiddleware
from apps.api.app.middleware.correlation import CorrelationIdMiddleware


def test_audit_log_minimal() -> None:
    app = FastAPI()
    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(AuditMiddleware)

    @app.get("/")
    async def index() -> dict[str, str]:
        return {"status": "ok"}

    captured: list[str] = []
    logger.remove()
    logger.add(lambda m: captured.append(m), serialize=True)

    client = TestClient(app, raise_server_exceptions=False)
    request_id = str(uuid.uuid4())
    response = client.get("/", headers={"X-Request-ID": request_id})
    assert response.status_code == 200

    record = json.loads(captured[0])["record"]["extra"]
    assert record["request_id"] == request_id
    assert record["route"] == "/"
    assert record.get("actor") is None
    assert record["tools_called"] == []
    assert record["egress"] == []
