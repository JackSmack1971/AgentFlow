"""Pydantic models for memory items."""

from __future__ import annotations

from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

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
    user_id: Optional[str] = None
    agent_id: Optional[str] = None
    session_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    ttl: Optional[int] = Field(None, ge=1, description="Time to live in seconds")


class MemoryItemCreate(MemoryItemBase):
    """Model for creating memory items."""


class MemoryItemUpdate(BaseModel):
    """Model for updating memory items."""

    text: Optional[str] = Field(None, min_length=1)
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    ttl: Optional[int] = Field(None, ge=1)


class MemoryItem(MemoryItemBase):
    """Full memory item model."""

    id: str
    embedding: List[float] = Field(default_factory=list)
    created_at: datetime
    expires_at: Optional[datetime] = None

    @validator("expires_at", always=True)
    def set_expires_at(
        cls, value: Optional[datetime], values: Dict[str, Any]
    ) -> Optional[datetime]:
        ttl = values.get("ttl")
        if value is None and ttl is not None:
            return values["created_at"] + timedelta(seconds=ttl)
        return value


class MemoryEvent(BaseModel):
    """Event emitted when memory changes."""

    action: Literal["created", "updated", "deleted"]
    item: MemoryItem
