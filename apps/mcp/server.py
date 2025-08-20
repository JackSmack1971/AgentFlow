from __future__ import annotations

import asyncio
import os

from loguru import logger
from mcp.server.fastmcp import Context, FastMCP

mcp = FastMCP("AgentFlow MCP", debug=False, log_level="INFO")


@mcp.tool()
async def ping(ctx: Context) -> str:
    """Health check tool."""
    await ctx.info("pong")
    return "pong"


def run_stdio() -> None:
    mcp.run()


async def run_http() -> None:
    """Stub HTTP transport."""
    logger.info("HTTP transport not yet implemented")


if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    if transport == "http":
        asyncio.run(run_http())
    else:
        run_stdio()
