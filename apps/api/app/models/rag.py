"""Response models for RAG operations."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class RAGSearchResponse(BaseModel):
    """Schema for responses returned by RAG search."""

    results: list[Any]


class DocumentUploadResponse(BaseModel):
    """Schema for responses after uploading a document."""

    ok: bool
