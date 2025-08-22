from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from loguru import logger
from pydantic import BaseModel


class AuditLogError(Exception):
    """Raised when audit logging fails."""


class AuditEvent(BaseModel):
    ts: datetime
    request_id: Optional[str] = None
    actor: Optional[str] = None
    route: str
    tools_called: List[str] = []
    egress: List[str] = []
    error: Optional[str] = None


def log_audit(event: AuditEvent) -> None:
    """Emit a structured audit log entry."""
    try:
        payload = event.model_dump(mode="json", exclude_none=True)
        logger.info("audit", **payload)
    except Exception as exc:  # pragma: no cover - best effort
        raise AuditLogError("Audit logging failed.") from exc
