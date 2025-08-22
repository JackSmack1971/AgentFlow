"""Tests for rate limit handler Retry-After header."""

from typing import Iterator

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from apps.api.app.main import rate_limit_handler
from apps.api.app.rate_limiter import limiter


@pytest.fixture(autouse=True)
def reset_limiter() -> Iterator[None]:
    limiter.reset()
    yield
    limiter.reset()


def test_retry_after_header() -> None:
    app = FastAPI()
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_handler)
    app.add_middleware(SlowAPIMiddleware)

    @app.get("/limited")
    @limiter.limit("1/minute")
    async def limited(request: Request) -> dict[str, str]:
        return {"status": "ok"}

    client = TestClient(app, raise_server_exceptions=False)
    client.get("/limited")
    resp = client.get("/limited")
    assert resp.status_code == 429
    assert "Retry-After" in resp.headers
    assert resp.headers["Retry-After"].isdigit()
