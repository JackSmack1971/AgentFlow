from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable

from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from ..observability.tracing import add_request_id_to_current_span
from ..utils.logging import request_id_ctx_var


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
        header_value = request.headers.get(self.header_name)
        try:
            if header_value:
                request_id = str(uuid.UUID(header_value))
            else:
                request_id = str(uuid.uuid4())
        except ValueError:
            request_id = str(uuid.uuid4())
        request.state.correlation_id = request_id
        token = request_id_ctx_var.set(request_id)
        add_request_id_to_current_span()
        try:
            response = await call_next(request)
            add_request_id_to_current_span()
        except Exception as exc:  # pragma: no cover - passthrough
            logger.error("correlation_error", error=str(exc))
            raise CorrelationIdError("Request handling failed") from exc
        finally:
            request_id_ctx_var.reset(token)
        response.headers[self.header_name] = request_id
        return response
