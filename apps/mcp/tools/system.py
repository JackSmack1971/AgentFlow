from __future__ import annotations

import logging
from typing import Any

from mcp.server.fastmcp import Context

from .middleware import with_middleware
from .registry import registry
from .schemas import HealthResponse, ToolsListResponse

logger = logging.getLogger(__name__)


class ToolsListError(Exception):
    """Raised when tools_list fails."""


class ToolsHealthError(Exception):
    """Raised when tools_health fails."""


@registry.register("tools_list")
@with_middleware("tools_list", timeout_s=2)
async def tools_list(ctx: Context[Any, Any, Any]) -> ToolsListResponse:
    """Return list of registered tools."""
    try:
        tools = registry.list_tools()
        await ctx.info("listed tools")
        return ToolsListResponse(tools=tools)
    except Exception as exc:  # pragma: no cover - unexpected
        await ctx.error(f"Tools list failed: {exc}")
        raise ToolsListError(str(exc)) from exc


@registry.register("tools_health")
@with_middleware("tools_health", timeout_s=2)
async def tools_health(ctx: Context[Any, Any, Any]) -> HealthResponse:
    """Simple health check."""
    try:
        await ctx.info("health ok")
        return HealthResponse(status="ok")
    except Exception as exc:  # pragma: no cover - unexpected
        await ctx.error(f"Health check failed: {exc}")
        raise ToolsHealthError(str(exc)) from exc
