"""Module executed when running ``python -m git_helper``."""

from __future__ import annotations

from .cli import main

__all__ = ["main"]

if __name__ == "__main__":
    main()
