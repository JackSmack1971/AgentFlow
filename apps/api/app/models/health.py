"""Pydantic models for health checks."""

from typing import Literal

from .base import StrictModel


class HealthStatus(StrictModel):
    """Represents the health status of the service."""

    status: Literal["ok", "ready"]
