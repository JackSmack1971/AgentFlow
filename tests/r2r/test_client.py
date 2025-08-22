import httpx
import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from packages.r2r.client import R2RClient
from packages.r2r.config import R2RConfig
from packages.r2r.errors import AuthError
from packages.r2r.models import DocV1


@pytest.fixture(autouse=True)
def _tracer() -> InMemorySpanExporter:
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    return exporter


def _client(handler: httpx.MockTransport) -> R2RClient:
    config = R2RConfig(base_url="http://test")
    return R2RClient(config=config, transport=handler)


@pytest.mark.asyncio
async def test_search_success(_tracer: InMemorySpanExporter) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/search"
        return httpx.Response(200, json={"hits": []})

    client = _client(httpx.MockTransport(handler))
    await client.search("query")
    spans = _tracer.get_finished_spans()
    assert spans and spans[0].name == "r2r.request"
    await client.close()


@pytest.mark.asyncio
async def test_index_idempotency() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Idempotency-Key"] == "abc"
        return httpx.Response(200, json={"id": "1", "status": "ok"})

    client = _client(httpx.MockTransport(handler))
    ack = await client.index(DocV1(content="x"), idempotency_key="abc")
    assert ack.status == "ok"
    await client.close()


@pytest.mark.asyncio
async def test_retry_and_error() -> None:
    attempts = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        attempts["n"] += 1
        if attempts["n"] < 2:
            return httpx.Response(503)
        return httpx.Response(401)

    client = _client(httpx.MockTransport(handler))
    with pytest.raises(AuthError):
        await client.search("hello")
    assert attempts["n"] == 2
    await client.close()
