"""Top-level exports for the gitHelper toolkit."""

from __future__ import annotations

from .api import GitHelperAPI
from .diagnostics import DiagnosticEngine
from .git_core import GitCore
from .plugin_manager import PluginManager
from .repo_manager import RepoManager

__all__ = [
    "__version__",
    "GitHelperAPI",
    "GitCore",
    "RepoManager",
    "PluginManager",
    "DiagnosticEngine",
]

__version__ = "2.0.0"
