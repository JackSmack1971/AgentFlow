from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class DocV1(BaseModel):
    content: str
    metadata: dict[str, Any] | None = None


class SearchHitV1(BaseModel):
    id: str
    score: float
    snippet: str


class SearchResultV1(BaseModel):
    hits: list[SearchHitV1] = Field(default_factory=list)


class IndexAckV1(BaseModel):
    id: str
    status: str


__all__ = [
    "DocV1",
    "SearchHitV1",
    "SearchResultV1",
    "IndexAckV1",
]
