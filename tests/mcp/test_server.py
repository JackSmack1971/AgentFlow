"""Tests for MCP server tools."""

from __future__ import annotations

import asyncio
import inspect
from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest
from mcp.server.fastmcp import Context
from mcp.server.fastmcp.exceptions import ToolError

from apps.mcp.server import mcp, run_http
from apps.mcp.tools.middleware import RateLimitError, ToolExecutionError
from apps.mcp.tools.ping import ping_tool
from apps.mcp.tools.rag_search import rag_search_tool
from apps.mcp.tools.schemas import RagSearchRequest
from apps.mcp.tools.system import tools_health, tools_list


@pytest.fixture
def mock_context() -> AsyncMock:
    """Provide a mocked MCP context."""
    ctx: AsyncMock = AsyncMock(spec=Context)
    ctx.info = AsyncMock()
    ctx.error = AsyncMock()
    return ctx


@pytest.fixture
def rag_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set required environment variables for RAG search."""
    monkeypatch.setenv("RAG_API_URL", "http://rag")


@pytest.fixture
def mock_rag_response(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    """Mock HTTP calls for RAG search tool."""
    mock_resp = Mock()
    mock_resp.json.return_value = {"answer": "hi", "sources": ["doc1"]}
    mock_resp.raise_for_status = Mock()
    mock_ac = AsyncMock()
    mock_ac.post.return_value = mock_resp

    class MockClient:
        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

        async def __aenter__(self) -> AsyncMock:
            return mock_ac

        async def __aexit__(
            self,
            exc_type: type[BaseException] | None,
            exc: BaseException | None,
            tb: Any | None,
        ) -> None:
            return None

    monkeypatch.setattr("apps.mcp.tools.rag_search.httpx.AsyncClient", MockClient)
    return mock_ac


@pytest.mark.asyncio
async def test_tool_discovery() -> None:
    """Tools should include registered commands."""
    tools = await mcp.list_tools()
    names = {tool.name for tool in tools}
    assert {"ping", "rag_search", "tools_list", "tools_health"}.issubset(names)


@pytest.mark.asyncio
async def test_ping_execution(mock_context: AsyncMock) -> None:
    """Ping tool should return pong and log info."""
    result = await ping_tool(mock_context)
    assert result.message == "pong"
    mock_context.info.assert_called()


@pytest.mark.asyncio
async def test_unknown_tool_error() -> None:
    """Unknown tools should raise ToolError."""
    with pytest.raises(ToolError):
        await mcp.call_tool("unknown", {})


@pytest.mark.asyncio
async def test_run_http() -> None:
    """HTTP transport stub should execute without error."""
    await run_http()
    assert True


@pytest.mark.asyncio
async def test_tools_list(mock_context: AsyncMock) -> None:
    """tools_list should return allowlisted tool names."""
    result = await tools_list(mock_context)
    assert {"ping", "rag_search", "tools_list", "tools_health"} == set(result.tools)
    mock_context.info.assert_called()


@pytest.mark.asyncio
async def test_tools_health(mock_context: AsyncMock) -> None:
    """tools_health should report status ok."""
    result = await tools_health(mock_context)
    assert result.status == "ok"
    mock_context.info.assert_called()


@pytest.mark.asyncio
async def test_rag_search_tool_success(
    mock_context: AsyncMock, rag_env: None, mock_rag_response: AsyncMock
) -> None:
    """rag_search_tool should return data from mocked API."""
    request = RagSearchRequest(query="hello", top_k=1)
    result = await rag_search_tool(mock_context, request)
    assert result.answer == "hi"
    assert result.sources == ["doc1"]
    mock_context.info.assert_called()
    mock_rag_response.post.assert_called()


@pytest.mark.asyncio
async def test_rate_limiting(
    mock_context: AsyncMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Exceeding rate limit should raise error."""
    limiter = inspect.getclosurevars(ping_tool).nonlocals["limiter"]
    limiter.tool_calls.clear()
    limiter.global_calls.clear()
    monkeypatch.setattr(limiter, "per_tool_limit", 1)
    monkeypatch.setattr(limiter, "global_limit", 1)
    await ping_tool(mock_context)
    with pytest.raises(RateLimitError):
        await ping_tool(mock_context)


@pytest.mark.asyncio
async def test_timeout_handling(mock_context: AsyncMock) -> None:
    """Slow tool should raise TimeoutError via middleware."""
    assert ping_tool.__closure__ is not None
    original_func = ping_tool.__closure__[0].cell_contents
    original_timeout = ping_tool.__closure__[3].cell_contents

    async def slow(ctx: Context[Any, Any, Any]) -> None:
        await asyncio.sleep(0.2)

    ping_tool.__closure__[0].cell_contents = slow
    ping_tool.__closure__[3].cell_contents = 0.01
    with pytest.raises(ToolExecutionError) as excinfo:
        await ping_tool(mock_context)
    assert isinstance(excinfo.value.__cause__, asyncio.TimeoutError)
    ping_tool.__closure__[0].cell_contents = original_func
    ping_tool.__closure__[3].cell_contents = original_timeout
