"""Logging helpers for gitHelper."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

try:  # pragma: no cover - optional dependency
    from rich.logging import RichHandler
except ModuleNotFoundError:  # pragma: no cover
    RichHandler = None  # type: ignore

LOG_DIR = Path.home() / ".githelper" / "logs"

__all__ = ["configure_logging", "get_logger", "LOG_DIR"]


def _log_file() -> Path:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    return LOG_DIR / f"githelper-{timestamp}.log"


def configure_logging(verbose: bool = False) -> None:
    """Configure application logging."""

    log_file = _log_file()
    handlers = []
    if RichHandler is not None:
        handlers.append(RichHandler(show_time=False, show_level=True))
    handlers.append(logging.FileHandler(log_file, encoding="utf-8"))
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(message)s",
        handlers=handlers,
        force=True,
    )
    logging.getLogger("github").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
