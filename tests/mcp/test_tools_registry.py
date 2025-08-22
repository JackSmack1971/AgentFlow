from typing import Any, Callable

import pytest

from apps.mcp.tools.registry import ToolRegistry


@pytest.mark.asyncio
async def test_registry_register_and_bind() -> None:
    registry = ToolRegistry()

    @registry.register("ping")
    async def ping(ctx: object) -> str:
        return "pong"

    class DummyMCP:
        def __init__(self) -> None:
            self.registered: dict[str, Callable[..., Any]] = {}

        def tool(self, name: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
            def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
                self.registered[name] = func
                return func

            return decorator

    mcp = DummyMCP()
    registry.bind(mcp)
    assert "ping" in registry.list_tools()
    assert "ping" in mcp.registered


@pytest.mark.asyncio
async def test_registry_allowlist() -> None:
    registry = ToolRegistry(allowlist={"allowed"})

    with pytest.raises(ValueError):

        @registry.register("blocked")
        async def blocked(ctx: object) -> str:
            return "nope"
