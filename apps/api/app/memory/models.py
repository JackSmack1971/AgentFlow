"""Pydantic models for memory items."""

from __future__ import annotations

from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, validator


class MemoryScope(str, Enum):
    """Available memory scopes."""

    USER = "user"
    AGENT = "agent"
    SESSION = "session"
    GLOBAL = "global"


class MemoryItemBase(BaseModel):
    """Base fields shared by memory models."""

    text: str = Field(..., min_length=1)
    scope: MemoryScope = MemoryScope.USER
    user_id: str | None = None
    agent_id: str | None = None
    session_id: str | None = None
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    ttl: int | None = Field(None, ge=1, description="Time to live in seconds")


class MemoryItemCreate(MemoryItemBase):
    """Model for creating memory items."""


class MemoryItemUpdate(BaseModel):
    """Model for updating memory items."""

    text: str | None = Field(None, min_length=1)
    tags: list[str] | None = None
    metadata: dict[str, Any] | None = None
    ttl: int | None = Field(None, ge=1)


class MemoryItem(MemoryItemBase):
    """Full memory item model."""

    id: str
    embedding: list[float] = Field(default_factory=list)
    created_at: datetime
    expires_at: datetime | None = None

    @validator("expires_at", always=True)
    def set_expires_at(
        cls, value: datetime | None, values: dict[str, Any]
    ) -> datetime | None:
        ttl = values.get("ttl")
        if value is None and ttl is not None:
            return values["created_at"] + timedelta(seconds=ttl)
        return value


class MemoryEvent(BaseModel):
    """Event emitted when memory changes."""

    action: Literal["created", "updated", "deleted"]
    item: MemoryItem