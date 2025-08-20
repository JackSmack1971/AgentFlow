from pydantic import BaseModel
from typing import Optional, Literal, List

class MemoryItem(BaseModel):
    id: Optional[str] = None
    text: str
    scope: Literal["user","agent","session","global"] = "user"
    user_id: Optional[str] = None
    agent_id: Optional[str] = None
    run_id: Optional[str] = None
    metadata: dict | None = None

class RAGQuery(BaseModel):
    query: str
    use_kg: bool = True
    limit: int = 25

class AgentPrompt(BaseModel):
    prompt: str
