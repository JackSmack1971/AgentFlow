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
        last_err: Exception | None = None
        for attempt in range(1, self._retries + 1):
            start = time.perf_counter()
            span = tracer.start_span("r2r.request")
            span.set_attribute("path", path)
            span.set_attribute("attempt", attempt)
            try:
                response = await self._client.request(
                    method,
                    path,
                    json=json,
                    headers=headers,
                    timeout=self._timeout,
                )
                status = response.status_code
                span.set_attribute("status_code", status)
                span.set_attribute("duration_ms", (time.perf_counter() - start) * 1000)
                if 200 <= status < 300:
                    span.end()
                    return response.json()
                last_err = self._map_error(status)
                span.end()
                if status < 500 and status != 429:
                    break
            except httpx.TimeoutException as exc:
                span.set_attribute("status_code", 0)
                span.set_attribute("duration_ms", (time.perf_counter() - start) * 1000)
                last_err = TimeoutError(str(exc))
                span.end()
            except httpx.HTTPError as exc:  # pragma: no cover - network errors
                span.set_attribute("status_code", 0)
                span.set_attribute("duration_ms", (time.perf_counter() - start) * 1000)
                last_err = UnavailableError(str(exc))
                span.end()
            if attempt == self._retries:
                break
            await asyncio.sleep(self._backoff(attempt))
        if last_err is None:
            raise UnavailableError("Unknown error")
        raise last_err

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
