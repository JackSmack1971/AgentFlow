from fastapi import APIRouter, Depends
from ..dependencies import require_roles, User
from ..models.schemas import AgentPrompt
from ..services.agents import run_agent

router = APIRouter()

@router.post("/run", summary="Run agent")
async def run(payload: AgentPrompt, user: User = Depends(require_roles(["user"]))):
    return {"result": await run_agent(payload.prompt)}
