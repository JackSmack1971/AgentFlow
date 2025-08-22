from typing import Any, Literal

from pydantic import field_validator

from .base import StrictModel


class MemoryItem(StrictModel):
    id: str | None = None
    text: str
    scope: Literal["user", "agent", "session", "global"] = "user"
    user_id: str | None = None
    agent_id: str | None = None
    run_id: str | None = None
    metadata: dict[str, Any] | None = None


class RAGQuery(StrictModel):
    query: str
    filters: dict[str, str] | None = None
    vector: bool = True
    keyword: bool = True
    graph: bool = True
    limit: int = 25

    @field_validator("filters")
    @classmethod
    def validate_filters(
        cls,
        value: dict[str, str] | None,
    ) -> dict[str, str] | None:
        if value is None:
            return None
        if any(
            (
                not isinstance(k, str) or not isinstance(v, str)
                for k, v in value.items()
            ),
        ):
            raise ValueError("filters must be string key-value pairs")
        return value


class AgentPrompt(StrictModel):
    prompt: str


class AgentRunResponse(StrictModel):
    result: str
