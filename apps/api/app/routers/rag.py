from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from ..dependencies import User, require_roles
from ..exceptions import R2RServiceError
from ..models.rag import DocumentUploadResponse, RAGSearchResponse
from ..models.schemas import RAGQuery
from ..services.rag import rag, rag_service

router = APIRouter()


@router.post("/", summary="Run RAG search", response_model=RAGSearchResponse)
async def run_rag(
    payload: RAGQuery, user: User = Depends(require_roles(["user"]))
) -> RAGSearchResponse:
    try:
        result = await rag(
            payload.query,
            filters=payload.filters,
            vector=payload.vector,
            keyword=payload.keyword,
            graph=payload.graph,
            limit=payload.limit,
        )
        return RAGSearchResponse.model_validate(result)
    except R2RServiceError as exc:  # pragma: no cover - error path
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post(
    "/documents",
    summary="Upload document to R2R",
    response_model=DocumentUploadResponse,
)
async def upload_document(
    file: UploadFile = File(...),
    user: User = Depends(require_roles(["user"])),
) -> DocumentUploadResponse:
    content = await file.read()
    filename = file.filename or "upload"
    content_type = file.content_type or "application/octet-stream"
    try:
        result = await rag_service.upload_document(
            content, filename=filename, content_type=content_type
        )
        return DocumentUploadResponse.model_validate(result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except R2RServiceError as exc:  # pragma: no cover - error path
        raise HTTPException(status_code=502, detail=str(exc)) from exc
