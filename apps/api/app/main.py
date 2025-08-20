from fastapi import FastAPI

from .config import get_settings
from .middleware import AuditMiddleware
from .routers import agents, auth, health, memory, rag
from .utils.logging import setup_logging

settings = get_settings()
setup_logging(settings.log_level)
app = FastAPI(title=settings.app_name, openapi_url=settings.openapi_url)
app.add_middleware(AuditMiddleware)

# Routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(memory.router, prefix="/memory", tags=["memory"])
app.include_router(rag.router, prefix="/rag", tags=["rag"])
app.include_router(agents.router, prefix="/agents", tags=["agents"])
app.include_router(health.router)
