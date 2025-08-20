from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from .config import get_settings
from .middleware import AuditMiddleware
from .rate_limiter import limiter
from .routers import agents, auth, cache_examples, health, memory, rag
from .utils.logging import setup_logging


class RateLimitError(Exception):
    """Raised when handling a rate limit response fails."""


async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Return a JSON response for rate limit violations."""
    try:
        return JSONResponse(status_code=429, content={"detail": "Too many requests"})
    except Exception as err:  # pragma: no cover - safety
        raise RateLimitError("Rate limit handler failed") from err

settings = get_settings()
setup_logging(settings.log_level)
app = FastAPI(title=settings.app_name, openapi_url=settings.openapi_url)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(AuditMiddleware)

# Routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(memory.router, prefix="/memory", tags=["memory"])
app.include_router(rag.router, prefix="/rag", tags=["rag"])
app.include_router(agents.router, prefix="/agents", tags=["agents"])
app.include_router(health.router)
app.include_router(cache_examples.router, tags=["cache"])
