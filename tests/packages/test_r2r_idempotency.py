import httpx
import pytest
import respx

from packages.r2r.client import R2RClient
from packages.r2r.models import DocV1


@respx.mock
@pytest.mark.asyncio
async def test_index_idempotency() -> None:
    """R2RClient should honor Idempotency-Key when indexing."""
    processed: dict[str | None, dict[str, str]] = {}
    processed_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal processed_count
        key = request.headers.get("Idempotency-Key")
        if key in processed:
            return httpx.Response(200, json=processed[key])
        processed_count += 1
        body = {"id": f"doc-{processed_count}", "status": "ok"}
        if key:
            processed[key] = body
        return httpx.Response(200, json=body)

    respx.post("http://localhost:7272/index").mock(side_effect=handler)
    client = R2RClient()
    doc = DocV1(content="hello")

    try:
        first = await client.index(doc, idempotency_key="same")
        second = await client.index(doc, idempotency_key="same")
        assert first == second
        assert processed_count == 1

        third = await client.index(doc)
        fourth = await client.index(doc)
        assert third.id != fourth.id
        assert processed_count == 3
    finally:
        await client.close()
