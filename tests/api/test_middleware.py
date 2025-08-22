import uuid

from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.api.app.middleware.body_size import BodySizeLimitMiddleware
from apps.api.app.middleware.correlation import CorrelationIdMiddleware


def _create_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(BodySizeLimitMiddleware, max_body_size=10)

    @app.post("/")
    async def echo(data: dict) -> dict:  # pragma: no cover - trivial
        return data

    return app


def test_correlation_header_added() -> None:
    app = _create_app()
    client = TestClient(app)
    resp = client.post("/", json={"a": "b"})
    assert resp.status_code == 200
    uuid.UUID(resp.headers["X-Request-ID"])


def test_body_size_limit_triggered() -> None:
    app = _create_app()
    client = TestClient(app)
    resp = client.post("/", data="x" * 20, headers={"Content-Type": "application/json"})
    assert resp.status_code == 413
