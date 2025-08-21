"""Workflow API router."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..exceptions import WorkflowExecutionError
from ..services.workflow import WorkflowService

router = APIRouter()


class WorkflowRequest(BaseModel):
    """Request model for running a workflow."""

    workflow_id: str = Field(..., min_length=1)
    inputs: dict[str, Any] = Field(default_factory=dict)


class WorkflowResponse(BaseModel):
    """Response model containing workflow results."""

    result: dict[str, Any]


def get_service() -> WorkflowService:
    """Return a workflow service instance."""

    return WorkflowService()


@router.post("/run", response_model=WorkflowResponse)
async def run_workflow(
    req: WorkflowRequest, service: WorkflowService = Depends(get_service)
) -> WorkflowResponse:
    """Execute a workflow and return its result."""
    try:
        result = await service.execute(req.workflow_id, req.inputs)
    except WorkflowExecutionError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return WorkflowResponse(result=result)


__all__ = ["router", "get_service"]
