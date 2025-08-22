from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import User, require_roles
from ..exceptions import AgentFlowError
from ..models.schemas import AgentPrompt, AgentRunResponse
from ..services.agents import run_agent

router = APIRouter()


@router.post("/run", summary="Run agent", response_model=AgentRunResponse)
async def run(payload: AgentPrompt, user: User = Depends(require_roles(["user"]))):
    try:
        result = await run_agent(payload.prompt)
        return AgentRunResponse(result=result)
    except AgentFlowError as exc:  # pragma: no cover - error path
        raise HTTPException(status_code=500, detail=str(exc)) from exc
