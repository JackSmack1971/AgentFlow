from fastapi import APIRouter, Depends
from ..dependencies import get_current_user
from ..models.schemas import MemoryItem
from ..services import memory as mem
router = APIRouter()

@router.post("/", summary="Add memory")
async def add_memory(item: MemoryItem, user = Depends(get_current_user)):
    return await mem.add_memory(
        text=item.text,
        user_id=item.user_id or user["sub"],
        agent_id=item.agent_id,
        run_id=item.run_id,
        metadata=item.metadata,
    )

@router.get("/search", summary="Search memories")
async def search(q: str, limit: int = 10, user = Depends(get_current_user)):
    return await mem.search_memories(q, user_id=user["sub"], limit=limit)
