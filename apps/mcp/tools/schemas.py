from __future__ import annotations

from pydantic import BaseModel, Field


class PingResponse(BaseModel):
    """Response model for ping tool."""

    message: str


class RagSearchRequest(BaseModel):
    """Request model for RAG search."""

    query: str = Field(..., min_length=1)
    top_k: int = Field(5, ge=1, le=50)


class RagSearchResponse(BaseModel):
    """Response model for RAG search results."""

    answer: str
    sources: list[str]


class ToolsListResponse(BaseModel):
    """Response model listing available tools."""

    tools: list[str]


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
