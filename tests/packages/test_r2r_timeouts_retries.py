from unittest.mock import AsyncMock

import httpx
import pytest
import respx
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from packages.r2r.client import R2RClient
from packages.r2r.config import R2RConfig
from packages.r2r.errors import TimeoutError
from packages.r2r.models import SearchResultV1


@settings(
    max_examples=10,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(failures=st.integers(min_value=0, max_value=2))
@pytest.mark.asyncio
async def test_retries_on_503_then_success(
    monkeypatch: pytest.MonkeyPatch, failures: int
) -> None:
    client = R2RClient(config=R2RConfig(base_url="http://test"))
    monkeypatch.setattr(client, "_backoff", lambda _attempt: 0)
    responses = [httpx.Response(503)] * failures + [
        httpx.Response(200, json={"hits": []})
    ]
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post("http://test/search").mock(side_effect=responses)
        try:
            result = await client.search("query")
        finally:
            await client.close()
    assert isinstance(result, SearchResultV1)
    assert route.call_count == failures + 1


@pytest.mark.asyncio
async def test_timeout_raises_after_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    client = R2RClient(config=R2RConfig(base_url="http://test"))
    monkeypatch.setattr(client, "_backoff", lambda _attempt: 0)
    request_mock = AsyncMock(side_effect=httpx.TimeoutException("boom"))
    monkeypatch.setattr(client._client, "request", request_mock)
    with pytest.raises(TimeoutError):
        await client.search("query")
    assert request_mock.call_count == client._retries
    await client.close()
