from __future__ import annotations

import sys

from loguru import logger


def setup_logging(level: str = "INFO") -> None:
    """Configure JSON structured logging.

    Args:
        level: Minimum log level.
    """
    logger.remove()
    logger.add(sys.stdout, serialize=True, level=level)
