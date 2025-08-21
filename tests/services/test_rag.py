import json

import pytest
import respx
from httpx import Response, TimeoutException

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
async def test_rag_hybrid_search() -> None:
    route = respx.post(f"{rag_module.R2R_BASE}/api/retrieval/rag").mock(
        return_value=Response(200, json={"ok": True})
    )
    await rag_module.rag("hi", vector=True, keyword=True, graph=False)
    assert route.called
    data = json.loads(route.calls.last.request.content.decode())
    settings = data["search_settings"]
    assert settings["use_vector_search"]
    assert settings["use_keyword_search"]
    assert not settings["use_kg_search"]


@respx.mock
@pytest.mark.asyncio
async def test_rag_metadata_filtered() -> None:
    route = respx.post(f"{rag_module.R2R_BASE}/api/retrieval/rag").mock(
        return_value=Response(200, json={"ok": True})
    )
    await rag_module.rag("filter", filters={"tag": "unit"})
    sent = json.loads(route.calls.last.request.content.decode())
    assert sent["metadata_filters"] == {"tag": "unit"}


@respx.mock
@pytest.mark.asyncio
async def test_rag_semantic_search() -> None:
    route = respx.post(f"{rag_module.R2R_BASE}/api/retrieval/rag").mock(
        return_value=Response(200, json={"ok": True})
    )
    await rag_module.rag("semantic", vector=True, keyword=False, graph=False)
    data = json.loads(route.calls.last.request.content.decode())
    settings = data["search_settings"]
    assert settings["use_vector_search"]
    assert not settings["use_keyword_search"]
    assert not settings["use_kg_search"]


@respx.mock
@pytest.mark.asyncio
async def test_rag_retries_then_success() -> None:
    route = respx.post(f"{rag_module.R2R_BASE}/api/retrieval/rag").mock(
        side_effect=[Response(500), Response(200, json={"ok": True})]
    )
    result = await rag_module.rag("retry")
    assert result == {"ok": True}
    assert route.call_count == 2


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
async def test_upload_document_ingest_retry_success() -> None:
    ingest_route = respx.post(f"{rag_module.R2R_BASE}/api/ingest").mock(
        side_effect=[Response(500), Response(200, json={"id": "1"})]
    )
    respx.post(f"{rag_module.R2R_BASE}/api/index").mock(
        return_value=Response(200, json={"ok": True})
    )
    result = await rag_module.rag_service.upload_document(
        b"data", filename="a.txt", content_type="text/plain"
    )
    assert result == {"ok": True}
    assert ingest_route.call_count == 2


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


@respx.mock
@pytest.mark.asyncio
async def test_upload_document_ingest_failure() -> None:
    respx.post(f"{rag_module.R2R_BASE}/api/ingest").mock(
        side_effect=[Response(500), Response(500), Response(500)]
    )
    with pytest.raises(R2RServiceError):
        await rag_module.rag_service.upload_document(
            b"oops", filename="a.txt", content_type="text/plain"
        )


@pytest.mark.asyncio
async def test_upload_document_invalid_type() -> None:
    with pytest.raises(ValueError):
        await rag_module.rag_service.upload_document(
            b"data", filename="a.exe", content_type="application/octet-stream"
        )


@respx.mock
@pytest.mark.asyncio
async def test_rag_no_filters_not_sent() -> None:
    route = respx.post(f"{rag_module.R2R_BASE}/api/retrieval/rag").mock(
        return_value=Response(200, json={"ok": True})
    )
    await rag_module.rag("nofilters", filters=None)
    sent = json.loads(route.calls.last.request.content.decode())
    assert "metadata_filters" not in sent


@respx.mock
@pytest.mark.asyncio
async def test_rag_timeout_retries_then_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fast_sleep(_: float) -> None:  # pragma: no cover - patched
        return None

    monkeypatch.setattr(rag_module.asyncio, "sleep", fast_sleep)
    route = respx.post(f"{rag_module.R2R_BASE}/api/retrieval/rag").mock(
        side_effect=[TimeoutException("timeout"), Response(200, json={"ok": True})]
    )
    result = await rag_module.rag("timeout")
    assert result == {"ok": True}
    assert route.call_count == 2


@respx.mock
@pytest.mark.asyncio
async def test_rag_timeout_retries_and_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fast_sleep(_: float) -> None:  # pragma: no cover - patched
        return None

    monkeypatch.setattr(rag_module.asyncio, "sleep", fast_sleep)
    route = respx.post(f"{rag_module.R2R_BASE}/api/retrieval/rag").mock(
        side_effect=[
            TimeoutException("timeout"),
            TimeoutException("timeout"),
            TimeoutException("timeout"),
        ]
    )
    with pytest.raises(R2RServiceError):
        await rag_module.rag("timeout fail")
    assert route.call_count == 3


@pytest.mark.asyncio
async def test_rag_empty_query_validation() -> None:
    with pytest.raises(ValueError):
        await rag_module.rag("")


@pytest.mark.asyncio
async def test_rag_search_mode_validation() -> None:
    with pytest.raises(ValueError):
        await rag_module.rag("q", vector=False, keyword=False, graph=False)


@pytest.mark.asyncio
async def test_upload_document_too_large() -> None:
    oversized = b"a" * (rag_module.MAX_FILE_SIZE + 1)
    with pytest.raises(ValueError):
        await rag_module.rag_service.upload_document(
            oversized, filename="big.txt", content_type="text/plain"
        )


@respx.mock
@pytest.mark.asyncio
async def test_upload_and_retrieve_document() -> None:
    respx.post(f"{rag_module.R2R_BASE}/api/ingest").mock(
        return_value=Response(200, json={"id": "1"})
    )
    respx.post(f"{rag_module.R2R_BASE}/api/index").mock(
        return_value=Response(200, json={"ok": True})
    )
    respx.post(f"{rag_module.R2R_BASE}/api/retrieval/rag").mock(
        return_value=Response(200, json={"results": ["doc"]})
    )
    upload = await rag_module.rag_service.upload_document(
        b"content", filename="a.txt", content_type="text/plain"
    )
    assert upload == {"ok": True}
    result = await rag_module.rag("content")
    assert result == {"results": ["doc"]}
