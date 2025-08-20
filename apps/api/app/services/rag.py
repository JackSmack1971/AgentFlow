import asyncio
import os
from httpx import AsyncClient, HTTPError
from ..exceptions import R2RServiceError

R2R_BASE = os.getenv("R2R_BASE_URL", "http://localhost:7272")
R2R_API_KEY = os.getenv("R2R_API_KEY", "")

async def rag(query: str, use_kg: bool = True, limit: int = 25) -> dict:
    if not query.strip():
        raise ValueError("query cannot be empty")
    payload = {
        "query": query,
        "rag_generation_config": {"model": "gpt-4o-mini", "temperature": 0.0},
        "search_settings": {"use_hybrid_search": True, "use_kg_search": use_kg, "limit": limit},
    }
    headers = {"Authorization": f"Bearer {R2R_API_KEY}"} if R2R_API_KEY else {}
    for attempt in range(3):
        try:
            async with AsyncClient(timeout=10) as client:
                resp = await client.post(f"{R2R_BASE}/api/retrieval/rag", json=payload, headers=headers)
                resp.raise_for_status()
                return resp.json()
        except HTTPError as exc:  # noqa: BLE001
            if attempt == 2:
                raise R2RServiceError("R2R request failed") from exc
            await asyncio.sleep(2 ** attempt)
