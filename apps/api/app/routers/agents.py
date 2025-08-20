from fastapi import APIRouter, Depends
from ..dependencies import get_current_user
from ..models.schemas import AgentPrompt
from ..services.agents import run_agent
router = APIRouter()

@router.post("/run", summary="Run agent")
async def run(payload: AgentPrompt, user = Depends(get_current_user)):
    return {"result": await run_agent(payload.prompt)}
