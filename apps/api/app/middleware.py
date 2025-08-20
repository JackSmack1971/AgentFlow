"""FastAPI middleware for audit logging and correlation IDs."""

from __future__ import annotations

import json
import time
import uuid
from contextlib import suppress

from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class MiddlewareError(Exception):
    """Custom exception for middleware errors."""


class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        correlation_id = str(uuid.uuid4())
        request.state.correlation_id = correlation_id
        body = await request.body()
        request._body = body
        start = time.time()
        try:
            response = await call_next(request)
        except Exception as exc:  # pragma: no cover - passthrough
            logger.error(
                "middleware_error", correlation_id=correlation_id, error=str(exc)
            )
            raise MiddlewareError("Request processing failed") from exc
        duration = (time.time() - start) * 1000
        event = "auth" if request.url.path.startswith("/auth") else "request"
        email = None
        if event == "auth":
            with suppress(Exception):  # pragma: no cover - best effort
                email = json.loads(body.decode()).get("email")
            response.headers["X-Correlation-ID"] = correlation_id
        logger.info(
            "audit",
            event=event,
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            email=email,
            duration_ms=round(duration, 2),
            correlation_id=correlation_id,
        )
        return response
