"""Pydantic models for cache operations."""

from .base import StrictModel


class CacheEntry(StrictModel):
    """Represents a cached key-value pair."""

    key: str
    value: str
    cached: bool


class CachePostResponse(StrictModel):
    """Response model for cached POST requests."""

    id: str
    value: str
    cached: bool
