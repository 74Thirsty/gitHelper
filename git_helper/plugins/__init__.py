"""Built-in plug-ins shipped with gitHelper."""

from __future__ import annotations

from .diffsummarizer_bot import register as register_diffsummarizer
from .code_break_analyzer import register as register_code_break_analyzer

__all__ = ["register_diffsummarizer", "register_code_break_analyzer"]
