"""MCP server entry point for AgentFlow.

Imports tool modules so each registers itself with the global registry.
The registry is then bound to the ``FastMCP`` instance, and middleware
wrapping is applied within the tool modules for logging, timeouts, and
rate limiting.

Security features:
- JWT authentication validation
- Audit logging for compliance
- Input sanitization and validation
- Rate limiting per user
"""

from __future__ import annotations

import asyncio
import os

from loguru import logger
from mcp.server.fastmcp import FastMCP, Context

# Import tools and registry. Tools register themselves on import via the
# registry decorator and apply middleware from ``tools.middleware``.
try:  # pragma: no cover - fallback for script execution
    from apps.mcp.tools import ping, rag_search, system  # noqa: F401
    from apps.mcp.tools.registry import registry
except ModuleNotFoundError:  # pragma: no cover
    from tools import ping, rag_search, system  # type: ignore  # noqa: F401
    from tools.registry import registry  # type: ignore

class AuthenticatedFastMCP(FastMCP):
    """Extended FastMCP with authentication context support."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._auth_context = {}

    def set_auth_context(self, context: dict):
        """Set authentication context for the current request."""
        self._auth_context = context

    def get_auth_context(self) -> dict:
        """Get current authentication context."""
        return self._auth_context

    async def _call_tool_with_auth(self, name: str, arguments: dict, context: Context):
        """Call tool with authentication context injected."""
        # Inject authentication context into the MCP context
        if hasattr(context, 'state'):
            context.state.update(self._auth_context)

        # Add user info to context for security decorators
        if 'user_info' in self._auth_context:
            context.user_info = self._auth_context['user_info']

        return await super()._call_tool(name, arguments, context)


mcp = AuthenticatedFastMCP("AgentFlow MCP", debug=False, log_level="INFO")
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
