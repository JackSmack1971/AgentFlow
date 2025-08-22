import pytest

from apps.mcp.tools.schemas import (
    HealthResponse,
    PingResponse,
    RagSearchRequest,
    RagSearchResponse,
    ToolsListResponse,
)


def test_ping_response() -> None:
    model = PingResponse(message="pong")
    assert model.message == "pong"


def test_rag_search_request_validation() -> None:
    with pytest.raises(ValueError):
        RagSearchRequest(query="", top_k=0)
    req = RagSearchRequest(query="q", top_k=5)
    assert req.top_k == 5


def test_rag_search_response() -> None:
    resp = RagSearchResponse(answer="a", sources=["s"])
    assert resp.sources == ["s"]


def test_tools_list_response() -> None:
    resp = ToolsListResponse(tools=["t"])
    assert resp.tools == ["t"]


def test_health_response() -> None:
    resp = HealthResponse(status="ok")
    assert resp.status == "ok"
