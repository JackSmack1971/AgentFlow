import httpx
import pytest
import respx
from hypothesis import given, settings
from hypothesis import strategies as st

from packages.r2r.client import R2RClient
from packages.r2r.config import R2RConfig
from packages.r2r.errors import (
    AuthError,
    BadRequestError,
    R2RError,
    RateLimitedError,
    TimeoutError,
    UnavailableError,
)


def _expected_error(status: int) -> type[R2RError]:
    if status == 400:
        return BadRequestError
    if status in {401, 403}:
        return AuthError
    if status == 429:
        return RateLimitedError
    if status in {408, 504}:
        return TimeoutError
    return UnavailableError


status_strategy = st.one_of(
    st.sampled_from([400, 401, 403, 408, 429]),
    st.integers(min_value=500, max_value=599),
)


@respx.mock
@settings(max_examples=25, deadline=None)
@given(status=status_strategy)
@pytest.mark.asyncio
async def test_search_error_mapping(status: int) -> None:
    respx.post("http://test/search").mock(
        side_effect=lambda _request: httpx.Response(status)
    )
    client = R2RClient(config=R2RConfig(base_url="http://test"))
    try:
        with pytest.raises(_expected_error(status)):
            await client.search("query")
    finally:
        await client.close()
