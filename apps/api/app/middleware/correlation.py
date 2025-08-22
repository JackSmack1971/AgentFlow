from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable

from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class CorrelationIdError(Exception):
    """Raised when correlation ID processing fails."""


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Attach a correlation ID header to all requests and responses."""

    header_name = "X-Request-ID"

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = request.headers.get(self.header_name, str(uuid.uuid4()))
        request.state.correlation_id = request_id
        try:
            response = await call_next(request)
        except Exception as exc:  # pragma: no cover - passthrough
            logger.error("correlation_error", error=str(exc))
            raise CorrelationIdError("Request handling failed") from exc
        response.headers[self.header_name] = request_id
        return response
