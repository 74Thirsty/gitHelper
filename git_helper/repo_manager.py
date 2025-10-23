"""Workspace discovery utilities for gitHelper frontends."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

from .directory import RepositoryDirectoryManager

__all__ = ["RepoManager"]


class RepoManager:
    """High level discovery helpers for repositories under management."""

    def __init__(self, base: Path | None = None) -> None:
        self.directory_manager = RepositoryDirectoryManager()
        if base is not None:
            self.directory_manager.change_directory(base, create=True)

    def repository_root(self) -> Path:
        return self.directory_manager.current_directory()

    def list(self) -> List[Path]:
        return self.directory_manager.list_repositories()

    def validate(self, path: str | Path) -> Path:
        candidate = Path(path).expanduser()
        if not candidate.exists():
            raise FileNotFoundError(f"Repository path {candidate} does not exist.")
        if not (candidate / ".git").is_dir():
            raise ValueError(f"{candidate} is not an initialised Git repository.")
        return candidate

    def scan(self, search_paths: Iterable[str | Path]) -> List[Path]:
        repositories: List[Path] = []
        for entry in search_paths:
            path = Path(entry).expanduser()
            if (path / ".git").is_dir():
                repositories.append(path)
        return sorted(repositories)

