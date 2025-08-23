import json
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

from packages.r2r.models import DocV1, IndexAckV1, SearchHitV1, SearchResultV1

DATA_PATH = Path(__file__).parent / "data" / "r2r_models.json"


def _roundtrip_bytes() -> bytes:
    """Return canonical JSON bytes for test data."""
    data = DATA_PATH.read_bytes()
    payload = json.loads(data)
    doc = DocV1.model_validate(payload["doc"])
    index_ack = IndexAckV1.model_validate(payload["index_ack"])
    search_result = SearchResultV1.model_validate(payload["search_result"])
    roundtrip = {
        "doc": doc.model_dump(),
        "index_ack": index_ack.model_dump(),
        "search_result": search_result.model_dump(),
    }
    return json.dumps(roundtrip, separators=(",", ":"), sort_keys=True).encode()


def test_json_roundtrip() -> None:
    """Deserializing and reserializing should match original bytes."""
    assert DATA_PATH.read_bytes() == _roundtrip_bytes()


doc_strategy = st.builds(
    DocV1,
    content=st.text(),
    metadata=st.none() | st.dictionaries(st.text(), st.integers() | st.text()),
)


@settings(max_examples=25, deadline=None)
@given(doc=doc_strategy)
def test_doc_roundtrip(doc: DocV1) -> None:
    """DocV1 should roundtrip through dump/validate."""
    assert DocV1.model_validate(doc.model_dump()) == doc


search_hit_strategy = st.builds(
    SearchHitV1,
    id=st.text(min_size=1),
    score=st.floats(allow_nan=False, allow_infinity=False),
    snippet=st.text(),
)
search_result_strategy = st.builds(
    SearchResultV1, hits=st.lists(search_hit_strategy, max_size=5)
)


@settings(max_examples=25, deadline=None)
@given(result=search_result_strategy)
def test_search_result_roundtrip(result: SearchResultV1) -> None:
    """SearchResultV1 should roundtrip through dump/validate."""
    assert SearchResultV1.model_validate(result.model_dump()) == result


index_ack_strategy = st.builds(
    IndexAckV1,
    id=st.text(min_size=1),
    status=st.text(min_size=1),
)


@settings(max_examples=25, deadline=None)
@given(ack=index_ack_strategy)
def test_index_ack_roundtrip(ack: IndexAckV1) -> None:
    """IndexAckV1 should roundtrip through dump/validate."""
    assert IndexAckV1.model_validate(ack.model_dump()) == ack
