"""Tests for MCP server tools."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from mcp.server.fastmcp import Context
from mcp.server.fastmcp.exceptions import ToolError

from apps.mcp.server import mcp, run_http
from apps.mcp.tools.ping import ping_tool


@pytest.fixture
def mock_context() -> AsyncMock:
    """Provide a mocked MCP context."""
    ctx: AsyncMock = AsyncMock(spec=Context)
    ctx.info = AsyncMock()
    ctx.error = AsyncMock()
    return ctx


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
