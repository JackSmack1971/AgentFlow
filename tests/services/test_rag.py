import pytest
import respx
from httpx import Response

from apps.api.app.exceptions import R2RServiceError
from apps.api.app.services import rag as rag_module


@respx.mock
@pytest.mark.asyncio
async def test_rag_success() -> None:
    respx.post(f"{rag_module.R2R_BASE}/api/retrieval/rag").mock(
        return_value=Response(200, json={"ok": True})
    )
    result = await rag_module.rag("hello")
    assert result == {"ok": True}


@respx.mock
@pytest.mark.asyncio
async def test_rag_retries_and_fails() -> None:
    respx.post(f"{rag_module.R2R_BASE}/api/retrieval/rag").mock(
        side_effect=[Response(500), Response(500), Response(500)]
    )
    with pytest.raises(R2RServiceError):
        await rag_module.rag("boom")


@respx.mock
@pytest.mark.asyncio
async def test_upload_document_success() -> None:
    respx.post(f"{rag_module.R2R_BASE}/api/ingest").mock(
        return_value=Response(200, json={"id": "1"})
    )
    respx.post(f"{rag_module.R2R_BASE}/api/index").mock(
        return_value=Response(200, json={"ok": True})
    )
    result = await rag_module.rag_service.upload_document(
        b"hello", filename="a.txt", content_type="text/plain"
    )
    assert result == {"ok": True}


@respx.mock
@pytest.mark.asyncio
async def test_upload_document_index_failure() -> None:
    respx.post(f"{rag_module.R2R_BASE}/api/ingest").mock(
        return_value=Response(200, json={"id": "1"})
    )
    respx.post(f"{rag_module.R2R_BASE}/api/index").mock(
        side_effect=[Response(500), Response(500), Response(500)]
    )
    with pytest.raises(R2RServiceError):
        await rag_module.rag_service.upload_document(
            b"bad", filename="a.txt", content_type="text/plain"
        )


@pytest.mark.asyncio
async def test_upload_document_invalid_type() -> None:
    with pytest.raises(ValueError):
        await rag_module.rag_service.upload_document(
            b"data", filename="a.exe", content_type="application/octet-stream"
        )
