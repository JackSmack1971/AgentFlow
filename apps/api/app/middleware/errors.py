"""Error handling middleware producing RFC 7807 responses."""

from __future__ import annotations

from typing import Dict, Type

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette import status

from ..errors import AgentFlowError, DomainError, ProviderError
from ..exceptions import (
    AuthenticationError,
    InvalidCredentialsError,
    OTPError,
    RBACError,
    TokenError,
)

EXCEPTION_STATUS: Dict[Type[AgentFlowError], int] = {
    AuthenticationError: status.HTTP_401_UNAUTHORIZED,
    InvalidCredentialsError: status.HTTP_401_UNAUTHORIZED,
    TokenError: status.HTTP_401_UNAUTHORIZED,
    OTPError: status.HTTP_400_BAD_REQUEST,
    RBACError: status.HTTP_403_FORBIDDEN,
    DomainError: status.HTTP_400_BAD_REQUEST,
    ProviderError: status.HTTP_502_BAD_GATEWAY,
    AgentFlowError: status.HTTP_500_INTERNAL_SERVER_ERROR,
}


def _problem_response(
    request: Request, exc: AgentFlowError, status_code: int
) -> JSONResponse:
    """Build RFC 7807 problem detail response."""
    code = exc.code.value
    content = {
        "type": f"/errors/{code}",
        "title": exc.__class__.__name__,
        "status": status_code,
        "detail": exc.message,
        "instance": str(request.url),
        "code": code,
    }
    return JSONResponse(status_code=status_code, content=content)


def register_error_handlers(app: FastAPI) -> None:
    """Register exception handlers on the FastAPI app."""
    for exc_type, status_code in EXCEPTION_STATUS.items():

        async def handler(
            request: Request, exc: AgentFlowError, *, status_code: int = status_code
        ) -> JSONResponse:
            try:
                return _problem_response(request, exc, status_code)
            except Exception:  # pragma: no cover - safety
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={
                        "type": "/errors/internal",
                        "title": "InternalServerError",
                        "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "detail": "Internal Server Error",
                        "instance": str(request.url),
                    },
                )

        app.add_exception_handler(exc_type, handler)
