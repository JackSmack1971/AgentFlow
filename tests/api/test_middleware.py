import json
import uuid

from fastapi import FastAPI
from fastapi.testclient import TestClient
from loguru import logger
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from starlette.requests import Request

trace.set_tracer_provider(TracerProvider())


def _create_app() -> FastAPI:
    from apps.api.app.middleware.body_size import BodySizeLimitMiddleware
    from apps.api.app.middleware.correlation import CorrelationIdMiddleware

    app = FastAPI()
    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(BodySizeLimitMiddleware, max_body_size=10)

    @app.post("/")
    async def echo(data: dict) -> dict:  # pragma: no cover - trivial
        return data

    return app


def _create_error_app() -> FastAPI:
    from apps.api.app.exceptions import MemoryServiceError
    from apps.api.app.middleware.errors import register_error_handlers

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
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.post("/", json={"a": "b"})
    assert resp.status_code == 200
    uuid.UUID(resp.headers["X-Request-ID"])


def test_body_size_limit_triggered() -> None:
    app = _create_app()
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.post(
        "/",
        data="x" * 20,
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 413


def test_error_handler_success() -> None:
    app = _create_error_app()
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_error_handler_problem_detail() -> None:
    app = _create_error_app()
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get("/boom")
    body = resp.json()
    assert resp.status_code == 400
    assert body["title"] == "MemoryServiceError"
    assert body["status"] == 400
    assert body["code"] == "D002"
    assert body["type"].endswith("D002")


def test_request_id_propagates_to_logs_and_spans() -> None:
    from apps.api.app.middleware.correlation import CorrelationIdMiddleware
    from apps.api.app.utils.logging import logger_with_request_id

    from apps.api.app.observability.tracing import (  # noqa: E501  # isort: skip
        add_request_id_to_current_span,
    )

    app = FastAPI()
    app.add_middleware(CorrelationIdMiddleware)

    # tracing configured at module import

    @app.get("/")
    async def index() -> dict[str, str]:
        with trace.get_tracer("test").start_as_current_span("handler") as span:
            add_request_id_to_current_span()
            logger_with_request_id().info("ping")
            span_request_id = span.attributes.get("request_id")
        return {"ok": "ok", "span_request_id": span_request_id}

    captured: list[str] = []
    logger.remove()
    logger.add(lambda m: captured.append(m), serialize=True)

    client = TestClient(app, raise_server_exceptions=False)
    request_id = str(uuid.uuid4())
    resp = client.get("/", headers={"X-Request-ID": request_id})

    assert resp.status_code == 200
    log_record = json.loads(captured[0])
    assert log_record["record"]["extra"]["request_id"] == request_id
    assert resp.json()["span_request_id"] == request_id


def test_audit_middleware_logs_event() -> None:
    from apps.api.app.middleware.audit import AuditMiddleware
    from apps.api.app.middleware.correlation import CorrelationIdMiddleware

    app = FastAPI()
    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(AuditMiddleware)

    @app.get("/")
    async def index(request: Request) -> dict[str, str]:
        request.state.actor = "alice"
        request.state.tools_called = ["tool"]
        request.state.egress = ["https://example.com"]
        return {"status": "ok"}

    captured: list[str] = []
    logger.remove()
    logger.add(lambda m: captured.append(m), serialize=True)

    client = TestClient(app, raise_server_exceptions=False)
    request_id = str(uuid.uuid4())
    resp = client.get("/", headers={"X-Request-ID": request_id})
    assert resp.status_code == 200

    record = json.loads(captured[0])
    extra = record["record"]["extra"]
    assert extra["request_id"] == request_id
    assert extra["actor"] == "alice"
    assert extra["route"] == "/"
    assert extra["tools_called"] == ["tool"]
    assert extra["egress"] == ["https://example.com"]
    assert extra.get("error") is None
    assert "ts" in extra


def test_audit_middleware_logs_error() -> None:
    from apps.api.app.middleware.audit import AuditMiddleware
    from apps.api.app.middleware.correlation import CorrelationIdMiddleware

    app = FastAPI()
    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(AuditMiddleware)

    @app.get("/boom")
    async def boom(request: Request) -> None:  # pragma: no cover - explicit
        request.state.actor = "bob"
        raise RuntimeError("boom")

    captured: list[str] = []
    logger.remove()
    logger.add(lambda m: captured.append(m), serialize=True)

    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get("/boom")
    assert resp.status_code == 500

    record = json.loads(captured[-1])
    extra = record["record"]["extra"]
    assert extra.get("actor") == "bob"
    assert extra.get("error") == "Request handling failed"
    assert extra["route"] == "/boom"
