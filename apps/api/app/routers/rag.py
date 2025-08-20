from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import User, require_roles
from ..exceptions import R2RServiceError
from ..models.schemas import RAGQuery
from ..services.rag import rag

router = APIRouter()


@router.post("/", summary="Run RAG search")
async def run_rag(payload: RAGQuery, user: User = Depends(require_roles(["user"]))):
    try:
        return await rag(payload.query, use_kg=payload.use_kg, limit=payload.limit)
    except R2RServiceError as exc:  # pragma: no cover - error path
        raise HTTPException(status_code=502, detail=str(exc)) from exc
