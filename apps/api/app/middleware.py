"""FastAPI middleware for audit logging."""
from __future__ import annotations

import json
import time

from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        body = await request.body()
        request._body = body
        start = time.time()
        response = await call_next(request)
        duration = (time.time() - start) * 1000
        event = "auth" if request.url.path.startswith("/auth") else "request"
        email = None
        if event == "auth":
            try:
                email = json.loads(body.decode()).get("email")
            except Exception:  # pragma: no cover - best effort
                email = None
        logger.info(
            "audit",
            event=event,
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            email=email,
            duration_ms=round(duration, 2),
        )
        return response
