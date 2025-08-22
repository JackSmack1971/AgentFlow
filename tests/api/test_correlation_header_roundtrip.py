import uuid

from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.api.app.middleware.correlation import CorrelationIdMiddleware


def test_correlation_header_roundtrip() -> None:
    app = FastAPI()
    app.add_middleware(CorrelationIdMiddleware)

    @app.get("/")
    async def index() -> dict[str, str]:
        return {"status": "ok"}

    client = TestClient(app, raise_server_exceptions=False)
    request_id = str(uuid.uuid4())
    response = client.get("/", headers={"X-Request-ID": request_id})
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == request_id
