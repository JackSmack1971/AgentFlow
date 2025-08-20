from fastapi import APIRouter, Depends
from ..dependencies import get_current_user
from ..models.schemas import RAGQuery
from ..services.rag import rag
router = APIRouter()

@router.post("/", summary="Run RAG search")
async def run_rag(payload: RAGQuery, user = Depends(get_current_user)):
    return await rag(payload.query, use_kg=payload.use_kg, limit=payload.limit)
