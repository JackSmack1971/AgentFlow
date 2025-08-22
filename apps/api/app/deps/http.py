from __future__ import annotations

import time
from typing import Any

import httpx
from loguru import logger
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from ..config import get_settings


class HttpClientError(Exception):
    """Raised when an HTTP request fails."""


class CircuitBreakerError(HttpClientError):
    """Raised when the circuit breaker is open."""


class CircuitBreaker:
    """Simple time-based circuit breaker."""

    def __init__(self, max_failures: int, reset_seconds: int) -> None:
        self.max_failures = max_failures
        self.reset_seconds = reset_seconds
        self.failures = 0
        self.opened_at: float | None = None

    def allow(self) -> bool:
        if self.opened_at is None:
            return True
        if time.monotonic() - self.opened_at > self.reset_seconds:
            self.failures = 0
            self.opened_at = None
            return True
        return False

    def record_failure(self) -> None:
        self.failures += 1
        if self.failures >= self.max_failures:
            self.opened_at = time.monotonic()


breaker: CircuitBreaker | None = None
_client: httpx.AsyncClient | None = None


async def startup_http_client() -> None:
    settings = get_settings()
    global breaker, _client
    breaker = CircuitBreaker(
        settings.http_cb_failure_threshold, settings.http_cb_reset_seconds
    )
    _client = httpx.AsyncClient(timeout=settings.http_timeout)


async def shutdown_http_client() -> None:
    if _client:
        await _client.aclose()


def get_http_client() -> httpx.AsyncClient:
    if _client is None:
        raise RuntimeError("HTTP client not initialized")
    return _client


async def request(method: str, url: str, **kwargs: Any) -> httpx.Response:
    if breaker is None:
        raise RuntimeError("HTTP client not initialized")
    if not breaker.allow():
        raise CircuitBreakerError("Circuit breaker open")
    client = get_http_client()
    settings = get_settings()
    try:
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(settings.http_max_retries),
            wait=wait_exponential_jitter(initial=0.1, max=1),
            retry=retry_if_exception_type(httpx.HTTPError),
        ):
            with attempt:
                response = await client.request(method, url, **kwargs)
        breaker.failures = 0
        return response
    except Exception as exc:  # noqa: BLE001
        breaker.record_failure()
        logger.error("http_request_failed", error=str(exc))
        raise HttpClientError("HTTP request failed") from exc
