"""RAG service layer."""

from __future__ import annotations

import asyncio
import os
from typing import Optional

from httpx import AsyncClient, HTTPError

from ..exceptions import R2RServiceError


R2R_BASE = os.getenv("R2R_BASE_URL", "http://localhost:7272")
R2R_API_KEY = os.getenv("R2R_API_KEY", "")


class RAGService:
    """Service for interacting with the R2R retrieval API."""

    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None) -> None:
        self.base_url = base_url or R2R_BASE
        self.api_key = api_key or R2R_API_KEY

    async def query(self, query: str, *, use_kg: bool = True, limit: int = 25) -> dict:
        if not query.strip():
            raise ValueError("query cannot be empty")
        payload = {
            "query": query,
            "rag_generation_config": {"model": "gpt-4o-mini", "temperature": 0.0},
            "search_settings": {"use_hybrid_search": True, "use_kg_search": use_kg, "limit": limit},
        }
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        for attempt in range(3):
            try:
                async with AsyncClient(timeout=10) as client:
                    resp = await client.post(
                        f"{self.base_url}/api/retrieval/rag",
                        json=payload,
                        headers=headers,
                    )
                    resp.raise_for_status()
                    return resp.json()
            except HTTPError as exc:  # noqa: BLE001
                if attempt == 2:
                    raise R2RServiceError("R2R request failed") from exc
                await asyncio.sleep(2**attempt)


rag_service = RAGService()


async def rag(query: str, use_kg: bool = True, limit: int = 25) -> dict:
    """Compatibility wrapper for existing imports."""

    return await rag_service.query(query, use_kg=use_kg, limit=limit)


__all__ = ["RAGService", "rag_service", "rag"]

