from __future__ import annotations

import json
import time
from collections.abc import Awaitable, Callable
from contextlib import suppress

from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class MiddlewareError(Exception):
    """Custom exception for audit middleware errors."""


class AuditMiddleware(BaseHTTPMiddleware):
    """Log basic request audit information."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        correlation_id = getattr(request.state, "correlation_id", "")
        try:
            body = await request.body()
        except Exception as exc:  # pragma: no cover - best effort
            raise MiddlewareError("Failed to read body") from exc
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
