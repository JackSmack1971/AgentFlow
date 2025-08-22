import asyncio

import pytest

from apps.mcp.tools.middleware import (
    RateLimiter,
    RateLimitError,
    ToolExecutionError,
    scrub_log,
    with_middleware,
)


@pytest.mark.asyncio
async def test_rate_limiter_per_tool() -> None:
    limiter = RateLimiter(per_tool_limit=1, global_limit=10)
    await limiter.check("a")
    with pytest.raises(RateLimitError):
        await limiter.check("a")


@pytest.mark.asyncio
async def test_rate_limiter_global() -> None:
    limiter = RateLimiter(per_tool_limit=10, global_limit=1)
    await limiter.check("a")
    with pytest.raises(RateLimitError):
        await limiter.check("b")


def test_scrub_log_masks_secrets() -> None:
    secret = "A" * 32
    masked = scrub_log(f"token:{secret}")
    assert secret not in masked


@pytest.mark.asyncio
async def test_with_middleware_success() -> None:
    limiter = RateLimiter()

    @with_middleware("ok", 1, limiter)
    async def ping(ctx: object) -> str:
        return "pong"

    assert await ping(None) == "pong"


@pytest.mark.asyncio
async def test_with_middleware_timeout() -> None:
    limiter = RateLimiter()

    @with_middleware("slow", 0.1, limiter)
    async def slow(ctx: object) -> str:
        await asyncio.sleep(0.2)
        return "done"

    with pytest.raises(ToolExecutionError):
        await slow(None)


@pytest.mark.asyncio
async def test_with_middleware_rate_limit() -> None:
    limiter = RateLimiter(per_tool_limit=1, global_limit=1)

    @with_middleware("limited", 1, limiter)
    async def ping(ctx: object) -> str:
        return "pong"

    await ping(None)
    with pytest.raises(RateLimitError):
        await ping(None)
