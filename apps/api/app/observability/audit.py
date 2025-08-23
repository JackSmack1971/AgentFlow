from __future__ import annotations

from datetime import datetime

from loguru import logger
from pydantic import BaseModel


class AuditLogError(Exception):
    """Raised when audit logging fails."""


class AuditEvent(BaseModel):
    ts: datetime
    request_id: str | None = None
    actor: str | None = None
    route: str
    tools_called: list[str] = []
    egress: list[str] = []
    error: str | None = None


def log_audit(event: AuditEvent) -> None:
    """Emit a structured audit log entry."""
    try:
        payload = event.model_dump(mode="json", exclude_none=True)
        logger.info("audit", **payload)
    except Exception as exc:  # pragma: no cover - best effort
        raise AuditLogError("Audit logging failed.") from exc