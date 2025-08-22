from __future__ import annotations

import re
import sys
from contextvars import ContextVar
from typing import Any, cast

from loguru import logger
from loguru._logger import Logger

request_id_ctx_var: ContextVar[str | None] = ContextVar(
    "request_id",
    default=None,
)

SECRET_PATTERN = re.compile(r"[A-Za-z0-9]{32,}")


def _redact(record: dict[str, Any]) -> dict[str, Any]:
    """Redact potential secrets from log records."""
    record["message"] = SECRET_PATTERN.sub("***", record["message"])
    return record


def setup_logging(level: str = "INFO") -> None:
    """Configure JSON structured logging.

    Args:
        level: Minimum log level.
    """
    logger.remove()
    logger.add(
        sys.stdout,
        serialize=True,
        level=level,
        filter=cast(Any, _redact),
    )


def logger_with_request_id() -> Logger:
    """Return a logger bound with the current request ID if available."""
    request_id = request_id_ctx_var.get()
    bound = logger.bind(request_id=request_id) if request_id else logger
    return cast(Logger, bound)
