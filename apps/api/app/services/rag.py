"""RAG service layer."""

from __future__ import annotations

import asyncio
import os
from typing import Any

from httpx import AsyncClient, HTTPError

from ..exceptions import R2RServiceError

R2R_BASE = os.getenv("R2R_BASE_URL", "http://localhost:7272")
R2R_API_KEY = os.getenv("R2R_API_KEY", "")

ALLOWED_TYPES = {"text/plain", "text/markdown"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


class RAGService:
    """Service for interacting with the R2R retrieval API."""

    def __init__(self, base_url: str | None = None, api_key: str | None = None) -> None:
        self.base_url = base_url or R2R_BASE
        self.api_key = api_key or R2R_API_KEY

    async def query(
        self,
        query: str,
        *,
        filters: dict[str, str] | None = None,
        vector: bool = True,
        keyword: bool = True,
        graph: bool = True,
        limit: int = 25,
    ) -> dict[str, Any]:
        if not query.strip():
            raise ValueError("query cannot be empty")
        if not any((vector, keyword, graph)):
            raise ValueError("at least one search mode must be enabled")
        payload = {
            "query": query,
            "rag_generation_config": {"model": "gpt-4o-mini", "temperature": 0.0},
            "search_settings": {
                "use_vector_search": vector,
                "use_keyword_search": keyword,
                "use_kg_search": graph,
                "limit": limit,
            },
        }
        if filters:
            payload["metadata_filters"] = filters
        return await self._post_with_retry("/api/retrieval/rag", payload)

    async def _post_with_retry(
        self, endpoint: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        last_exc: HTTPError | None = None
        for attempt in range(3):
            try:
                async with AsyncClient(timeout=10) as client:
                    resp = await client.post(
                        f"{self.base_url}{endpoint}", json=payload, headers=headers
                    )
                    resp.raise_for_status()
                    return resp.json()
            except HTTPError as exc:  # noqa: BLE001
                last_exc = exc
                await asyncio.sleep(2**attempt)
        raise R2RServiceError(f"R2R request to {endpoint} failed") from last_exc

    async def upload_document(
        self,
        content: bytes,
        *,
        filename: str,
        content_type: str,
        chunk_size: int = 1000,
    ) -> dict[str, Any]:
        if content_type not in ALLOWED_TYPES:
            raise ValueError("unsupported file type")
        if len(content) > MAX_FILE_SIZE:
            raise ValueError("file too large")
        text = content.decode("utf-8", errors="ignore")
        chunks = [
            {
                "text": text[i : i + chunk_size],
                "metadata": {"source": filename, "chunk": i // chunk_size},
            }
            for i in range(0, len(text), chunk_size)
        ]
        ids = [
            (await self._post_with_retry("/api/ingest", chunk)).get("id")
            for chunk in chunks
        ]
        return await self._post_with_retry("/api/index", {"document_ids": ids})


rag_service = RAGService()


async def rag(
    query: str,
    *,
    filters: dict[str, str] | None = None,
    vector: bool = True,
    keyword: bool = True,
    graph: bool = True,
    limit: int = 25,
) -> dict[str, Any]:
    """Compatibility wrapper for existing imports."""

    return await rag_service.query(
        query,
        filters=filters,
        vector=vector,
        keyword=keyword,
        graph=graph,
        limit=limit,
    )


__all__ = ["RAGService", "rag_service", "rag"]
