"""Tests for MCP server tools."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from mcp.server.fastmcp import Context
from mcp.server.fastmcp.exceptions import ToolError

from apps.mcp.server import mcp, ping, run_http


@pytest.fixture
def mock_context() -> AsyncMock:
    """Provide a mocked MCP context."""
    ctx: AsyncMock = AsyncMock(spec=Context)
    ctx.info = AsyncMock()
    ctx.error = AsyncMock()
    return ctx


@pytest.mark.asyncio
async def test_tool_discovery() -> None:
    """Tools should include the ping command."""
    tools = await mcp.list_tools()
    assert any(tool.name == "ping" for tool in tools)


@pytest.mark.asyncio
async def test_ping_execution(mock_context: AsyncMock) -> None:
    """Ping tool should return pong and log info."""
    result = await ping(mock_context)
    assert result == "pong"
    mock_context.info.assert_called_with("pong")


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
