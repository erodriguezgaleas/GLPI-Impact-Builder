"""Logging configuration for GLPI Impact Builder."""

from pathlib import Path
from loguru import logger

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logger.remove()

logger.add(
    LOG_DIR / "glpi-impact.log",
    rotation="10 MB",
    retention="30 days",
    enqueue=True,
    level="DEBUG",
)

logger.add(lambda m: print(m, end=""), level="INFO")

__all__ = ["logger"]
