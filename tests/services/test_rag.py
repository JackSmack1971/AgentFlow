import pytest
import respx
from httpx import Response
from apps.api.app.services import rag as rag_service
from apps.api.app.exceptions import R2RServiceError

@respx.mock
@pytest.mark.asyncio
async def test_rag_success() -> None:
    respx.post(f"{rag_service.R2R_BASE}/api/retrieval/rag").mock(return_value=Response(200, json={"ok": True}))
    result = await rag_service.rag("hello")
    assert result == {"ok": True}

@respx.mock
@pytest.mark.asyncio
async def test_rag_retries_and_fails() -> None:
    respx.post(f"{rag_service.R2R_BASE}/api/retrieval/rag").mock(side_effect=[Response(500), Response(500), Response(500)])
    with pytest.raises(R2RServiceError):
        await rag_service.rag("boom")
