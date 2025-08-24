from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..dependencies import User, require_roles
from ..exceptions import AgentFlowError
from ..models.schemas import AgentPrompt, AgentRunResponse
from ..services.agents import run_agent
from ..services.saga import create_agent_saga, SagaError


class AgentCreateRequest(BaseModel):
    """Request model for creating a new agent."""
    name: str
    organization_id: UUID
    session_data: dict
    embeddings: List[float]
    relationships: List[dict] = []


class AgentCreateResponse(BaseModel):
    """Response model for agent creation."""
    transaction_id: str
    agent_id: UUID | None = None
    status: str
    error: str | None = None
    failed_step: str | None = None
    compensated: bool = False

router = APIRouter()


@router.post("/create", summary="Create agent with saga pattern", response_model=AgentCreateResponse)
async def create_agent(
    payload: AgentCreateRequest,
    user: User = Depends(require_roles(["admin", "user"]))
):
    """Create a new agent using the saga pattern for distributed transaction coordination.

    This endpoint demonstrates the saga pattern implementation that ensures data consistency
    across PostgreSQL, Redis, Qdrant, and Neo4j databases during agent creation.
    """
    try:
        # Prepare audit context
        audit_context = {
            "request_id": getattr(user, "request_id", None),
            "actor": str(user.id),
            "action": "create_agent"
        }

        # Execute saga transaction
        result = await create_agent_saga(
            organization_id=payload.organization_id,
            agent_data={"name": payload.name},
            session_data=payload.session_data,
            embeddings=payload.embeddings,
            relationships=payload.relationships,
            audit_context=audit_context
        )

        return AgentCreateResponse(**result)

    except SagaError as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(exc),
                "transaction_id": exc.transaction_id,
                "failed_step": exc.failed_step
            }
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during agent creation: {exc}"
        ) from exc


@router.post("/run", summary="Run agent", response_model=AgentRunResponse)
async def run(payload: AgentPrompt, user: User = Depends(require_roles(["user"]))):
    try:
        result = await run_agent(payload.prompt)
        return AgentRunResponse(result=result)
    except AgentFlowError as exc:  # pragma: no cover - error path
        raise HTTPException(status_code=500, detail=str(exc)) from exc
