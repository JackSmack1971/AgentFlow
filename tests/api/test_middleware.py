import uuid

from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.api.app.exceptions import MemoryServiceError
from apps.api.app.middleware.body_size import BodySizeLimitMiddleware
from apps.api.app.middleware.correlation import CorrelationIdMiddleware
from apps.api.app.middleware.errors import register_error_handlers


def _create_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(BodySizeLimitMiddleware, max_body_size=10)

    @app.post("/")
    async def echo(data: dict) -> dict:  # pragma: no cover - trivial
        return data

    return app


def _create_error_app() -> FastAPI:
    app = FastAPI()
    register_error_handlers(app)

    @app.get("/")
    async def ok() -> dict[str, str]:  # pragma: no cover - trivial
        return {"status": "ok"}

    @app.get("/boom")
    async def boom() -> None:  # pragma: no cover - explicit
        raise MemoryServiceError("fail")

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


def test_error_handler_success() -> None:
    app = _create_error_app()
    client = TestClient(app)
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_error_handler_problem_detail() -> None:
    app = _create_error_app()
    client = TestClient(app)
    resp = client.get("/boom")
    body = resp.json()
    assert resp.status_code == 400
    assert body["title"] == "MemoryServiceError"
    assert body["status"] == 400
    assert body["code"] == "D002"
    assert body["type"].endswith("D002")
