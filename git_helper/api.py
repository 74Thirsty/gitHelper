"""Unified facade exposing gitHelper backend capabilities."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from .diagnostics import DiagnosticEngine
from .git_core import GitCore
from .plugin_manager import PluginManager
from .repo_manager import RepoManager
from .ssh_tools import SSHTools

__all__ = ["GitHelperAPI"]


class GitHelperAPI:
    """Aggregate convenience facade for CLI and GUI frontends."""

    def __init__(self, path: str | Path | None = None) -> None:
        base = Path(path or Path.cwd())
        self.git = GitCore(base)
        self.repo_manager = RepoManager()
        self.ssh = SSHTools()
        self.plugins = PluginManager(self.git)
        self.diagnostics = DiagnosticEngine(self.git)

    # ----------------------------------------------------------------- git flows
    def status(self) -> str:
        return self.git.status()

    def recent_log(self, limit: int = 20) -> str:
        return self.git.log(limit=limit)

    def push(self, remote: str, branch: str, *, set_upstream: bool = False) -> str:
        return self.git.push(remote, branch, set_upstream=set_upstream)

    def pull(self, remote: str, branch: str) -> str:
        return self.git.pull(remote, branch)

    def commit(self, message: str) -> str:
        return self.git.commit(message)

    # ------------------------------------------------------------ repository ops
    def list_repositories(self) -> list[Path]:
        return self.repo_manager.list()

    # -------------------------------------------------------------- diagnostics
    def bisect(self, *, known_good: Optional[str] = None, known_bad: str = "HEAD") -> str:
        return self.diagnostics.find_breaking_commit(known_good=known_good, known_bad=known_bad)

    def summarize_diff(self, commit_hash: str) -> str:
        return self.diagnostics.summarize_diff(commit_hash)

    # -------------------------------------------------------------- plugin hooks
    def run_plugin(self, name: str, context: object | None = None) -> str:
        return self.plugins.run_plugin(name, context)

