"""Core plug-in protocol for gitHelper frontends."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(slots=True)
class Plugin:
    """Container describing a single plug-in entry point."""

    name: str
    description: str
    run: Callable[[Any, Any], str]


__all__ = ["Plugin"]
