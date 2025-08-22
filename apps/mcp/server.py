"""MCP server entry point for AgentFlow.

Imports tool modules so each registers itself with the global registry.
The registry is then bound to the ``FastMCP`` instance, and middleware
wrapping is applied within the tool modules for logging, timeouts, and
rate limiting.
"""

from __future__ import annotations

import asyncio
import os

from loguru import logger
from mcp.server.fastmcp import FastMCP

# Import tools and registry. Tools register themselves on import via the
# registry decorator and apply middleware from ``tools.middleware``.
try:  # pragma: no cover - fallback for script execution
    from apps.mcp.tools import ping, rag_search, system  # noqa: F401
    from apps.mcp.tools.registry import registry
except ModuleNotFoundError:  # pragma: no cover
    from tools import ping, rag_search, system  # type: ignore  # noqa: F401
    from tools.registry import registry  # type: ignore

mcp = FastMCP("AgentFlow MCP", debug=False, log_level="INFO")
# Bind all tools registered in the global registry to this MCP instance.
registry.bind(mcp)


def run_stdio() -> None:  # pragma: no cover
    """Run MCP server using STDIO transport."""
    mcp.run()


async def run_http() -> None:
    """Stub HTTP transport for future extension."""
    logger.info("HTTP transport not yet implemented")


if __name__ == "__main__":  # pragma: no cover
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    if transport == "http":
        asyncio.run(run_http())
    else:
        run_stdio()
