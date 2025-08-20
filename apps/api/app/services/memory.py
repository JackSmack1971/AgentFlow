import asyncio
import os
from ..exceptions import MemoryServiceError

try:  # pragma: no cover - dependency may be optional in tests
    from mem0 import Memory, MemoryClient  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    Memory = MemoryClient = None  # type: ignore

MEM0_MODE = os.getenv("MEM0_MODE", "oss")

if Memory is not None and MemoryClient is not None:
    if MEM0_MODE == "hosted":
        memory = MemoryClient(api_key=os.getenv("MEM0_API_KEY"))
    else:
        memory = Memory.from_config({
            "vector_store": {"provider": "qdrant", "config": {"host": "localhost", "port": 6333}},
            "llm": {"provider": "openai", "config": {"api_key": os.getenv("OPENAI_API_KEY", ""), "model": "gpt-4o-mini"}},
            "embedder": {"provider": "openai", "config": {"api_key": os.getenv("OPENAI_API_KEY", ""), "model": "text-embedding-3-small"}},
            "version": "v1.1",
        })
else:  # pragma: no cover
    memory = None

async def add_memory(
    text: str,
    user_id: str | None = None,
    agent_id: str | None = None,
    run_id: str | None = None,
    metadata: dict | None = None,
):
    if not text.strip():
        raise ValueError("text cannot be empty")
    if memory is None:
        raise MemoryServiceError("memory backend not available")
    try:
        return await asyncio.to_thread(
            memory.add,
            text,
            user_id=user_id,
            agent_id=agent_id,
            run_id=run_id,
            metadata=metadata or {},
        )
    except Exception as exc:  # noqa: BLE001
        raise MemoryServiceError("Failed to add memory") from exc

async def search_memories(
    query: str,
    user_id: str | None = None,
    agent_id: str | None = None,
    run_id: str | None = None,
    limit: int = 10,
):
    if not query.strip():
        raise ValueError("query cannot be empty")
    if memory is None:
        raise MemoryServiceError("memory backend not available")
    try:
        return await asyncio.to_thread(
            memory.search,
            query,
            user_id=user_id,
            agent_id=agent_id,
            run_id=run_id,
            limit=limit,
        )
    except Exception as exc:  # noqa: BLE001
        raise MemoryServiceError("Failed to search memories") from exc
