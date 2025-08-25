from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from ..dependencies import User, require_roles
from ..exceptions import R2RServiceError
from ..models.rag import DocumentUploadResponse, RAGSearchResponse
from ..models.schemas import RAGQuery
from ..services.circuit_breaker import ServiceUnavailableError
from ..services.input_validation import SecurityValidator
from ..services.rag import MAX_FILE_SIZE, rag, rag_service

router = APIRouter()


@router.post("/", summary="Run RAG search", response_model=RAGSearchResponse)
async def run_rag(
    payload: RAGQuery, user: User = Depends(require_roles(["user"]))
) -> RAGSearchResponse:
    try:
        # Security validation for prompt injection protection
        validator = SecurityValidator()
        validation_result = validator.validate_input(payload.query, "rag_query")

        if not validation_result["valid"]:
            raise HTTPException(
                status_code=400,
                detail=f"Query validation failed: {', '.join(validation_result['threats'])}"
            )

        # Use sanitized query instead of raw query
        sanitized_query = validation_result["sanitized"]

        result = await rag(
            sanitized_query,
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


async def scan_for_malware(content: bytes) -> bool:
    """
    Scan file content for malware patterns.

    TODO: Implement proper malware scanning with:
    - ClamAV integration
    - YARA rules
    - Content analysis
    - File type verification
    """
    # Placeholder implementation - check for obvious malicious patterns
    content_str = content.decode('utf-8', errors='ignore').lower()

    # Check for script tags and other malicious patterns
    malicious_patterns = [
        '<script', 'javascript:', 'vbscript:', 'onload=', 'onerror=',
        'eval(', 'exec(', 'system(', 'shell_exec('
    ]

    for pattern in malicious_patterns:
        if pattern in content_str:
            return True

    return False


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

    # ADD CONTENT VALIDATION
    content_type = file.content_type or "application/octet-stream"

    # Validate allowed content types
    allowed_types = {
        "text/plain", "text/csv", "application/pdf",
        "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    }

    if content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    # ADD MALWARE SCANNING (placeholder - implement proper scanning)
    if await scan_for_malware(bytes(content)):
        raise HTTPException(status_code=400, detail="File contains malicious content")

    filename = file.filename or "upload"
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
