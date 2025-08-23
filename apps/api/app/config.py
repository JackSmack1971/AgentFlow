"""Application settings helpers."""

from __future__ import annotations

# `Sequence` should come from collections.abc rather than typing per PEP 585.
from collections.abc import Sequence

from pydantic import ValidationError

from .core.settings import Settings, get_settings

# Names of required settings keys.  Using Sequence from collections.abc avoids
# deprecation warnings about the typing.Sequence alias.
REQUIRED_SETTINGS: Sequence[str] = (
    "secret_key",
    "database_url",
    "redis_url",
    "qdrant_url",
)


def validate_settings() -> Settings:
    """Return settings or raise if critical values are missing."""
    try:
        settings = get_settings()
    except ValidationError as exc:  # pragma: no cover - configuration
        raise RuntimeError("Invalid settings") from exc
    missing = [name for name in REQUIRED_SETTINGS if not getattr(settings, name)]
    if missing:
        joined = ", ".join(missing)
        raise RuntimeError(f"Missing required settings: {joined}")
    return settings