import time

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from .config import validate_settings
from .deps.http import shutdown_http_client, startup_http_client
from .middleware.audit import AuditMiddleware
from .middleware.body_size import BodySizeLimitMiddleware
from .middleware.correlation import CorrelationIdMiddleware
from .middleware.errors import register_error_handlers
from .observability.tracing import setup_tracing
from .rate_limiter import limiter
from .routers import agents, auth, cache_examples, health, memory, rag, workflow
from .utils.logging import setup_logging


class RateLimitError(Exception):
    """Raised when handling a rate limit response fails."""


DEFAULT_RETRY_AFTER = 60


async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """Return a JSON response for rate limit violations."""
    try:
        reset_time = getattr(exc, "reset_time", time.time() + DEFAULT_RETRY_AFTER)
        setattr(exc, "reset_time", reset_time)
        retry_after = max(int(reset_time - time.time()), 0)
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests"},
            headers={"Retry-After": str(retry_after)},
        )
    except Exception as err:  # pragma: no cover - safety
        raise RateLimitError("Rate limit handler failed") from err


settings = validate_settings()
setup_logging(settings.log_level)
setup_tracing(settings.app_name)
app = FastAPI(title=settings.app_name, openapi_url=settings.openapi_url)
register_error_handlers(app)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(BodySizeLimitMiddleware, max_body_size=settings.max_body_size)
app.add_middleware(AuditMiddleware)
app.add_event_handler("startup", startup_http_client)
app.add_event_handler("shutdown", shutdown_http_client)

# Routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(memory.router, prefix="/memory", tags=["memory"])
app.include_router(rag.router, prefix="/rag", tags=["rag"])
app.include_router(agents.router, prefix="/agents", tags=["agents"])
app.include_router(workflow.router, prefix="/workflow", tags=["workflow"])
app.include_router(health.router)
app.include_router(cache_examples.router, tags=["cache"])
