from unittest.mock import AsyncMock, patch

import pytest

import apps.mcp.tools.ping  # noqa: F401
from apps.mcp.tools.middleware import ToolExecutionError
from apps.mcp.tools.system import tools_health, tools_list


@pytest.mark.asyncio
async def test_tools_list_success() -> None:
    ctx = AsyncMock()
    resp = await tools_list(ctx)
    assert "ping" in resp.tools
    ctx.info.assert_called()


@pytest.mark.asyncio
async def test_tools_list_error() -> None:
    ctx = AsyncMock()
    with patch(
        "apps.mcp.tools.system.registry.list_tools", side_effect=Exception("fail")
    ):
        with pytest.raises(ToolExecutionError):
            await tools_list(ctx)
    ctx.error.assert_called()


@pytest.mark.asyncio
async def test_tools_health_success() -> None:
    ctx = AsyncMock()
    resp = await tools_health(ctx)
    assert resp.status == "ok"
    ctx.info.assert_called()


@pytest.mark.asyncio
async def test_tools_health_error() -> None:
    ctx = AsyncMock()
    ctx.info.side_effect = Exception("boom")
    with pytest.raises(ToolExecutionError):
        await tools_health(ctx)
    ctx.error.assert_called()
