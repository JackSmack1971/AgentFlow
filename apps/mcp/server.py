from __future__ import annotations

import asyncio
import os
from typing import Any

from loguru import logger
from mcp.server.fastmcp import Context, FastMCP

mcp = FastMCP("AgentFlow MCP", debug=False, log_level="INFO")


@mcp.tool()
async def ping(ctx: Context[Any, Any, Any]) -> str:
    """Health check tool."""
    await ctx.info("pong")
    return "pong"


def run_stdio() -> None:  # pragma: no cover
    mcp.run()


async def run_http() -> None:
    """Stub HTTP transport."""
    logger.info("HTTP transport not yet implemented")


if __name__ == "__main__":  # pragma: no cover
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    if transport == "http":
        asyncio.run(run_http())
    else:
        run_stdio()
