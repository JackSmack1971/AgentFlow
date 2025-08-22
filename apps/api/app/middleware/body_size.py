from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from ..config import get_settings


class BodySizeLimitError(Exception):
    """Raised when request body cannot be processed."""


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    """Reject requests with bodies exceeding configured limit."""

    def __init__(self, app: ASGIApp, max_body_size: int | None = None) -> None:
        super().__init__(app)
        settings = get_settings()
        self.max_body_size = max_body_size or settings.max_body_size

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        try:
            body = await request.body()
        except Exception as exc:  # pragma: no cover - best effort
            raise BodySizeLimitError("Failed to read request body") from exc
        if len(body) > self.max_body_size:
            return Response(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
        request._body = body
        return await call_next(request)
