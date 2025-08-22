from __future__ import annotations

import logging
from typing import Any

from mcp.server.fastmcp import Context

from .middleware import with_middleware
from .registry import registry
from .schemas import PingResponse

logger = logging.getLogger(__name__)


class PingError(Exception):
    """Raised when ping tool fails."""


@registry.register("ping")
@with_middleware("ping", timeout_s=2)
async def ping_tool(ctx: Context[Any, Any, Any]) -> PingResponse:
    """Simple health check tool."""
    try:
        await ctx.info("ping received")
        logger.info("responding to ping")
        return PingResponse(message="pong")
    except Exception as exc:  # pragma: no cover - unexpected
        await ctx.error(f"Ping failed: {exc}")
        raise PingError(str(exc)) from exc
