from typing import List
import os
from mem0 import Memory, MemoryClient

# Choose hosted vs OSS via env flag
MEM0_MODE = os.getenv("MEM0_MODE", "oss")

memory = None
if MEM0_MODE == "hosted":
    memory = MemoryClient(api_key=os.getenv("MEM0_API_KEY"))
else:
    # Minimal OSS config with Qdrant
    memory = Memory.from_config({
        "vector_store": {"provider": "qdrant", "config": {"host": "localhost", "port": 6333}},
        "llm": {"provider": "openai", "config": {"api_key": os.getenv("OPENAI_API_KEY",""), "model": "gpt-4o-mini"}},
        "embedder": {"provider": "openai", "config": {"api_key": os.getenv("OPENAI_API_KEY",""), "model": "text-embedding-3-small"}},
        "version": "v1.1"
    })

async def add_memory(text: str, user_id: str | None = None, agent_id: str | None = None, run_id: str | None = None, metadata: dict | None = None):
    return memory.add(text, user_id=user_id, agent_id=agent_id, run_id=run_id, metadata=metadata or {})

async def search_memories(query: str, user_id: str | None = None, agent_id: str | None = None, run_id: str | None = None, limit: int = 10):
    return memory.search(query, user_id=user_id, agent_id=agent_id, run_id=run_id, limit=limit)
