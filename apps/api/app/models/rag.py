"""Response models for RAG operations."""

from __future__ import annotations

from typing import Any

from .base import StrictModel


class RAGSearchResponse(StrictModel):
    """Schema for responses returned by RAG search."""

    results: list[Any]


class DocumentUploadResponse(StrictModel):
    """Schema for responses after uploading a document."""

    ok: bool
