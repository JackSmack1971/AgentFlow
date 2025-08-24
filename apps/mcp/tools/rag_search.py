from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

import httpx
from mcp.server.fastmcp import Context
from pydantic import AnyUrl, TypeAdapter, ValidationError

from .middleware import with_middleware
from .registry import registry
from .schemas import RagSearchRequest, RagSearchResponse
from .security import validate_input

logger = logging.getLogger(__name__)


class RagSearchError(Exception):
    """Raised when RAG search fails."""


def _get_rag_api_url() -> str:
    api_url_raw = os.getenv("RAG_API_URL")
    if not api_url_raw:
        raise RagSearchError("RAG_API_URL not set")
    try:
        return str(TypeAdapter(AnyUrl).validate_python(api_url_raw))
    except ValidationError as exc:
        raise RagSearchError(f"Invalid RAG_API_URL: {api_url_raw}") from exc


def _build_headers() -> dict[str, str]:
    headers: dict[str, str] = {}
    if api_key := os.getenv("RAG_API_KEY"):
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


@registry.register("rag_search")
@validate_input(query={"max_length": 1000, "required": True})
@with_middleware("rag_search", timeout_s=8)
async def rag_search_tool(
    ctx: Context[Any, Any, Any], request: RagSearchRequest
) -> RagSearchResponse:
    """Perform RAG search via external API with security validation."""
    # Input has already been validated and sanitized by the decorator
    api_url = _get_rag_api_url()
    headers = _build_headers()
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
        except (httpx.HTTPError, asyncio.TimeoutError) as exc:
            wait = 2**attempt
            logger.warning("rag search attempt %s failed: %s", attempt + 1, exc)
            if attempt == 2:
                msg = (
                    f"HTTP error: {exc}"
                    if isinstance(exc, httpx.HTTPError)
                    else "RAG search timed out"
                )
                await ctx.error(msg)
                raise RagSearchError(msg) from exc
            await asyncio.sleep(wait)
    raise RagSearchError("unknown error")  # pragma: no cover
