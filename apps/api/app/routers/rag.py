from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from ..dependencies import User, require_roles
from ..exceptions import R2RServiceError
from ..models.rag import DocumentUploadResponse, RAGSearchResponse
from ..models.schemas import RAGQuery
from ..services.circuit_breaker import ServiceUnavailableError
from ..services.rag import MAX_FILE_SIZE, rag, rag_service

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
    except ServiceUnavailableError as exc:  # pragma: no cover - circuit breaker open
        raise HTTPException(status_code=503, detail=str(exc)) from exc
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
    file_size = getattr(file, "size", None)
    if file_size is not None and file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds maximum size of {MAX_FILE_SIZE} bytes",
        )

    content = bytearray()
    while True:
        chunk = await file.read(1024 * 1024)
        if not chunk:
            break
        content.extend(chunk)
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File exceeds maximum size of {MAX_FILE_SIZE} bytes",
            )

    filename = file.filename or "upload"
    content_type = file.content_type or "application/octet-stream"
    try:
        result = await rag_service.upload_document(
            bytes(content), filename=filename, content_type=content_type
        )
        return DocumentUploadResponse.model_validate(result)
    except ServiceUnavailableError as exc:  # pragma: no cover - circuit breaker open
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except R2RServiceError as exc:  # pragma: no cover - error path
        raise HTTPException(status_code=502, detail=str(exc)) from exc
