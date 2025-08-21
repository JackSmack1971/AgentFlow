import pytest
from httpx import ASGITransport, AsyncClient

from apps.api.app.exceptions import R2RServiceError
from apps.api.app.main import app
from apps.api.app.routers import rag as rag_router


@pytest.mark.asyncio
async def test_run_rag_success(monkeypatch) -> None:
    async def fake_rag(query: str, use_kg: bool = True, limit: int = 25) -> dict:
        return {"results": []}

    monkeypatch.setattr(rag_router, "rag", fake_rag)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/rag/", json={"query": "hi", "use_kg": True, "limit": 5})
    assert resp.status_code == 200
    assert resp.json() == {"results": []}


@pytest.mark.asyncio
async def test_run_rag_failure(monkeypatch) -> None:
    async def fake_rag(query: str, use_kg: bool = True, limit: int = 25) -> dict:
        raise R2RServiceError("fail")

    monkeypatch.setattr(rag_router, "rag", fake_rag)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/rag/", json={"query": "bad", "use_kg": True, "limit": 5})
    assert resp.status_code == 502
    assert resp.json()["detail"] == "fail"


@pytest.mark.asyncio
async def test_upload_document_success(monkeypatch) -> None:
    async def fake_upload(content: bytes, *, filename: str, content_type: str) -> dict:
        return {"ok": True}

    monkeypatch.setattr(rag_router.rag_service, "upload_document", fake_upload)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/rag/documents",
            files={"file": ("a.txt", b"hello", "text/plain")},
        )
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}


@pytest.mark.asyncio
async def test_upload_document_service_error(monkeypatch) -> None:
    async def fake_upload(content: bytes, *, filename: str, content_type: str) -> dict:
        raise R2RServiceError("boom")

    monkeypatch.setattr(rag_router.rag_service, "upload_document", fake_upload)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/rag/documents",
            files={"file": ("a.txt", b"hello", "text/plain")},
        )
    assert resp.status_code == 502
    assert resp.json()["detail"] == "boom"


@pytest.mark.asyncio
async def test_upload_document_validation_error(monkeypatch) -> None:
    async def fake_upload(content: bytes, *, filename: str, content_type: str) -> dict:
        raise ValueError("bad")

    monkeypatch.setattr(rag_router.rag_service, "upload_document", fake_upload)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/rag/documents",
            files={"file": ("a.txt", b"hello", "text/plain")},
        )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "bad"
