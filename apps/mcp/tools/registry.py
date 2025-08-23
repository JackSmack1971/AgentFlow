from __future__ import annotations

from typing import Any
from collections.abc import Awaitable, Callable


class ToolRegistry:
    """Registry for MCP tools with allowlist enforcement."""

    def __init__(self, allowlist: set[str] | None = None) -> None:
        self.allowlist = allowlist
        self._tools: dict[str, Callable[..., Awaitable[Any]]] = {}

    def register(
        self, name: str
    ) -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]]:
        """Decorator to register a tool function."""

        def decorator(
            func: Callable[..., Awaitable[Any]],
        ) -> Callable[..., Awaitable[Any]]:
            if self.allowlist and name not in self.allowlist:
                raise ValueError(f"Tool '{name}' not allowed")
            self._tools[name] = func
            return func

        return decorator

    def bind(self, mcp: Any) -> None:
        """Bind registered tools to an MCP server instance."""
        for name, func in self._tools.items():
            mcp.tool(name=name)(func)

    def list_tools(self) -> list[str]:
        """Return list of registered tool names."""
        return list(self._tools.keys())


# Global registry instance for tool registration
registry = ToolRegistry()