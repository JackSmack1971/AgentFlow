from unittest.mock import AsyncMock

import pytest

from apps.mcp.tools.middleware import ToolExecutionError
from apps.mcp.tools.ping import ping_tool


@pytest.mark.asyncio
async def test_ping_tool_success() -> None:
    ctx = AsyncMock()
    resp = await ping_tool(ctx)
    assert resp.message == "pong"
    ctx.info.assert_called()


@pytest.mark.asyncio
async def test_ping_tool_error() -> None:
    ctx = AsyncMock()
    ctx.info.side_effect = Exception("boom")
    with pytest.raises(ToolExecutionError):
        await ping_tool(ctx)
    ctx.error.assert_called()
