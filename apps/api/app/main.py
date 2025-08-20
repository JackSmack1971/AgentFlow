from fastapi import FastAPI
from .config import get_settings
from .routers import auth, memory, rag, agents

settings = get_settings()
app = FastAPI(title=settings.app_name, openapi_url=settings.openapi_url)

# Routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(memory.router, prefix="/memory", tags=["memory"])
app.include_router(rag.router, prefix="/rag", tags=["rag"])
app.include_router(agents.router, prefix="/agents", tags=["agents"])

@app.get("/health")
async def health():
    return {"status": "ok"}
