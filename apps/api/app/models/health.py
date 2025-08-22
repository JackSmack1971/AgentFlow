"""Pydantic models for health checks."""

from typing import Literal

from pydantic import BaseModel


class HealthStatus(BaseModel):
    """Represents the health status of the service."""

    status: Literal["ok", "ready"]
