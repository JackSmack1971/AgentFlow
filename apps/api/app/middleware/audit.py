from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import datetime

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from ..observability.audit import AuditEvent, log_audit


class MiddlewareError(Exception):
    """Custom exception for audit middleware errors."""


class AuditMiddleware(BaseHTTPMiddleware):
    """Record structured audit logs for each request."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        try:
            response = await call_next(request)
        except Exception as exc:  # pragma: no cover - passthrough
            event = AuditEvent(
                ts=datetime.utcnow(),
                request_id=getattr(request.state, "correlation_id", ""),
                actor=getattr(request.state, "actor", None),
                route=request.url.path,
                tools_called=getattr(request.state, "tools_called", []),
                egress=getattr(request.state, "egress", []),
                error=str(exc),
            )
            log_audit(event)
            raise MiddlewareError("Request processing failed.") from exc
        event = AuditEvent(
            ts=datetime.utcnow(),
            request_id=getattr(request.state, "correlation_id", ""),
            actor=getattr(request.state, "actor", None),
            route=request.url.path,
            tools_called=getattr(request.state, "tools_called", []),
            egress=getattr(request.state, "egress", []),
            error=None,
        )
        log_audit(event)
        return response
