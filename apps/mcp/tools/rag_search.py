from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

import httpx
from mcp.server.fastmcp import Context

from .middleware import with_middleware
from .registry import registry
from .schemas import RagSearchRequest, RagSearchResponse

logger = logging.getLogger(__name__)


class RagSearchError(Exception):
    """Raised when RAG search fails."""


@registry.register("rag_search")
@with_middleware("rag_search", timeout_s=8)
async def rag_search_tool(
    ctx: Context[Any, Any, Any], request: RagSearchRequest
) -> RagSearchResponse:
    """Perform RAG search via external API."""
    api_url = os.getenv("RAG_API_URL")
    if not api_url:
        raise RagSearchError("RAG_API_URL not set")
    headers: dict[str, str] = {}
    api_key = os.getenv("RAG_API_KEY")
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    payload = request.model_dump()
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.post(api_url, json=payload, headers=headers)
                resp.raise_for_status()
                data: Any = resp.json()
                result = RagSearchResponse.model_validate(data)
                await ctx.info("rag search success")
                return result
        except Exception as exc:
            wait = 2**attempt
            logger.warning("rag search attempt %s failed: %s", attempt + 1, exc)
            if attempt == 2:
                await ctx.error(f"RAG search failed: {exc}")
                raise RagSearchError(str(exc)) from exc
            await asyncio.sleep(wait)
    raise RagSearchError("unknown error")  # pragma: no cover
