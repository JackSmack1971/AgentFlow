from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from apps.mcp.tools.middleware import ToolExecutionError
from apps.mcp.tools.rag_search import rag_search_tool
from apps.mcp.tools.schemas import RagSearchRequest


@pytest.mark.asyncio
async def test_rag_search_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RAG_API_URL", "http://rag")
    ctx = AsyncMock()
    request = RagSearchRequest(query="test")
    mock_resp = Mock()
    mock_resp.json.return_value = {"answer": "hi", "sources": ["doc1"]}
    mock_resp.raise_for_status = Mock()
    mock_ac = AsyncMock()
    mock_ac.post.return_value = mock_resp
    with patch("httpx.AsyncClient") as client:
        client.return_value.__aenter__.return_value = mock_ac
        result = await rag_search_tool(ctx, request)
    assert result.answer == "hi"
    assert result.sources == ["doc1"]
    ctx.info.assert_called()


@pytest.mark.asyncio
async def test_rag_search_invalid_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RAG_API_URL", "not-a-url")
    ctx = AsyncMock()
    request = RagSearchRequest(query="test")
    with pytest.raises(ToolExecutionError):
        await rag_search_tool(ctx, request)


@pytest.mark.asyncio
async def test_rag_search_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RAG_API_URL", "http://rag")
    ctx = AsyncMock()
    request = RagSearchRequest(query="fail")
    mock_ac = AsyncMock()
    mock_ac.post.side_effect = httpx.HTTPError("boom")
    with patch("httpx.AsyncClient") as client:
        client.return_value.__aenter__.return_value = mock_ac
        with pytest.raises(ToolExecutionError):
            await rag_search_tool(ctx, request)
    assert mock_ac.post.call_count == 3
    ctx.error.assert_called()
