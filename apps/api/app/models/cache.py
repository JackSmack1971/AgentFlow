"""Pydantic models for cache operations."""

from pydantic import BaseModel


class CacheEntry(BaseModel):
    """Represents a cached key-value pair."""

    key: str
    value: str
    cached: bool


class CachePostResponse(BaseModel):
    """Response model for cached POST requests."""

    id: str
    value: str
    cached: bool
