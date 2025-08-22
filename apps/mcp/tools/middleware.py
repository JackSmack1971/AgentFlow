from __future__ import annotations

import asyncio
import logging
import re
import time
from asyncio import Lock, TimeoutError
from collections import deque
from functools import wraps
from typing import Any, Awaitable, Callable, Deque, Dict

logger = logging.getLogger(__name__)
SECRET_PATTERN = re.compile(r"[A-Za-z0-9]{32,}")


class RateLimitError(Exception):
    """Raised when rate limits are exceeded."""


class ToolExecutionError(Exception):
    """Raised when tool execution fails."""


class ToolTimeout(ToolExecutionError):
    """Raised when a tool exceeds its timeout."""


class RateLimiter:
    """Simple sliding-window rate limiter."""

    def __init__(self, per_tool_limit: int = 60, global_limit: int = 60) -> None:
        self.per_tool_limit = per_tool_limit
        self.global_limit = global_limit
        self.tool_calls: Dict[str, Deque[float]] = {}
        self.global_calls: Deque[float] = deque()
        self.lock = Lock()

    async def check(self, name: str) -> None:
        async with self.lock:
            now = time.monotonic()
            cutoff = now - 60
            calls = self.tool_calls.setdefault(name, deque())
            while calls and calls[0] < cutoff:
                calls.popleft()
            while self.global_calls and self.global_calls[0] < cutoff:
                self.global_calls.popleft()
            if (
                len(calls) >= self.per_tool_limit
                or len(self.global_calls) >= self.global_limit
            ):
                raise RateLimitError(f"Rate limit exceeded for {name}")
            calls.append(now)
            self.global_calls.append(now)


def scrub_log(text: str) -> str:
    """Mask secrets in log messages."""
    return SECRET_PATTERN.sub("***", text)


def with_middleware(
    name: str, timeout_s: float, limiter: RateLimiter | None = None
) -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]]:
    """Decorator adding timeout, rate limiting, and logging."""
    limiter = limiter or RateLimiter()

    def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        @wraps(func)
        async def wrapper(ctx: Any, *args: Any, **kwargs: Any) -> Any:
            await limiter.check(name)
            logger.info(scrub_log(f"start {name}"))
            try:
                result = await asyncio.wait_for(
                    func(ctx, *args, **kwargs), timeout=timeout_s
                )
                logger.info(scrub_log(f"end {name}"))
                return result
            except RateLimitError:
                logger.error(scrub_log(f"rate limit {name}"))
                raise
            except TimeoutError as exc:
                logger.error(scrub_log(f"timeout {name}"))
                raise ToolTimeout("timeout") from exc
            except Exception as exc:
                logger.exception(scrub_log(f"error {name}: {exc}"))
                raise ToolExecutionError(str(exc)) from exc

        wrapper.__globals__.update(func.__globals__)  # type: ignore[attr-defined]
        return wrapper

    return decorator
