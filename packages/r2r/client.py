from __future__ import annotations

import asyncio
import random
import time
from typing import Any

import httpx
from opentelemetry import trace

from .config import R2RConfig, load_config
from .errors import (
    AuthError,
    BadRequestError,
    R2RError,
    RateLimitedError,
    TimeoutError,
    UnavailableError,
)
from .models import DocV1, IndexAckV1, SearchResultV1

tracer = trace.get_tracer(__name__)


class R2RClient:
    def __init__(
        self,
        config: R2RConfig | None = None,
        *,
        timeout: float = 10.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._config = config or load_config()
        self._timeout = timeout
        self._client = httpx.AsyncClient(
            base_url=self._config.base_url,
            headers=self._headers(),
            transport=transport,
        )
        self._retries = 3

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if self._config.api_key:
            headers["Authorization"] = f"Bearer {self._config.api_key}"
        return headers

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: Any | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        response = await self._send_with_retry(
            method, path, json=json, headers=headers
        )
        return self._parse_response(response)

    async def _send_with_retry(
        self,
        method: str,
        path: str,
        *,
        json: Any | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        last_err: Exception = UnavailableError("Unknown error")
        for attempt in range(1, self._retries + 1):
            span, start = self._start_span(path, attempt)
            try:
                response = await self._client.request(
                    method, path, json=json, headers=headers, timeout=self._timeout
                )
                self._record_span(span, start, response.status_code)
                if 200 <= response.status_code < 300:
                    return response
                last_err = self._map_error(response.status_code)
                if response.status_code < 500 and response.status_code != 429:
                    break
            except (httpx.TimeoutException, httpx.HTTPError) as exc:
                self._record_span(span, start, 0)
                last_err = TimeoutError(str(exc)) if isinstance(exc, httpx.TimeoutException) else UnavailableError(str(exc))
            if attempt < self._retries:
                await asyncio.sleep(self._backoff(attempt))
        raise last_err

    def _start_span(self, path: str, attempt: int) -> tuple[trace.Span, float]:
        span = tracer.start_span("r2r.request")
        span.set_attribute("path", path)
        span.set_attribute("attempt", attempt)
        return span, time.perf_counter()

    def _record_span(self, span: trace.Span, start: float, status: int) -> None:
        span.set_attribute("status_code", status)
        span.set_attribute("duration_ms", (time.perf_counter() - start) * 1000)
        span.end()

    def _parse_response(self, response: httpx.Response) -> Any:
        status = response.status_code
        if 200 <= status < 300:
            return response.json()
        raise self._map_error(status)

    def _map_error(self, status: int) -> R2RError:
        if status == 400:
            return BadRequestError("Bad request")
        if status in {401, 403}:
            return AuthError("Unauthorized")
        if status == 429:
            return RateLimitedError("Rate limited")
        if status in {408, 504}:
            return TimeoutError("Request timeout")
        return UnavailableError("Service unavailable")

    def _backoff(self, attempt: int) -> float:
        return min(2 ** (attempt - 1), 10) + random.random()  # nosec B311

    async def search(self, query: str, top_k: int = 10) -> SearchResultV1:
        if not query.strip():
            raise ValueError("query must not be empty")
        if top_k <= 0:
            raise ValueError("top_k must be positive")
        data = await self._request(
            "POST", "/search", json={"query": query, "top_k": top_k}
        )
        return SearchResultV1(**data)

    async def index(self, doc: DocV1, idempotency_key: str | None = None) -> IndexAckV1:
        headers = {}
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        data = await self._request(
            "POST", "/index", json=doc.model_dump(), headers=headers
        )
        return IndexAckV1(**data)

    async def close(self) -> None:
        await self._client.aclose()


__all__ = ["R2RClient"]
