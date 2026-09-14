"""Central logging configuration."""

import logging
import sys

from app.core.config import get_settings


def configure_logging() -> None:
    """Configure application-wide structured logging to stdout."""
    settings = get_settings()
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        stream=sys.stdout,
        force=True,
    )
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
