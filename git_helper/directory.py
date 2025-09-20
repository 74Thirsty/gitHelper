"""Repository directory management utilities."""

from __future__ import annotations

from pathlib import Path
from typing import List

from .config import load_config, save_config
from .errors import DirectoryError

__all__ = ["RepositoryDirectoryManager"]


class RepositoryDirectoryManager:
    """Manage the directory where repositories are stored."""

    def __init__(self) -> None:
        self._config = load_config()

    def refresh(self) -> None:
        """Reload configuration values from disk."""

        self._config = load_config()

    # ------------------------------------------------------------------ helpers
    def _resolve(self, path: str | Path) -> Path:
        resolved = Path(path).expanduser()
        try:
            return resolved.resolve()
        except FileNotFoundError:
            # Path.resolve fails on non-existent paths when strict=True (default
            # prior to Python 3.12); fall back to absolute() to keep behaviour
            # consistent across Python versions.
            return resolved.absolute()

    # ---------------------------------------------------------------- directory
    def current_directory(self) -> Path:
        """Return the configured repository root directory."""

        configured = self._config.get("repository_root")
        if not configured:
            raise DirectoryError("Repository directory is not configured.")
        return self._resolve(configured)

    def change_directory(self, new_path: str | Path, *, create: bool = False) -> Path:
        """Update the configured repository directory.

        Args:
            new_path: The target directory to store repositories in.
            create: When ``True`` the directory is created if it does not
                already exist.

        Returns:
            The resolved directory path.
        """

        path = self._resolve(new_path)
        if path.exists() and not path.is_dir():
            raise DirectoryError(f"{path} exists but is not a directory.")
        if not path.exists():
            if not create:
                raise DirectoryError(
                    f"{path} does not exist. Pass create=True to create it."
                )
            try:
                path.mkdir(parents=True, exist_ok=True)
            except OSError as exc:  # pragma: no cover - platform specific
                raise DirectoryError(f"Unable to create {path}: {exc}") from exc

        config = load_config()
        config["repository_root"] = str(path)
        save_config(config)
        self._config = config
        return path

    # ------------------------------------------------------------------ queries
    def list_repositories(self) -> List[Path]:
        """Return directories beneath the repository root that are Git repos."""

        base = self.current_directory()
        if not base.exists():
            raise DirectoryError(
                f"Configured repository directory {base} is not accessible."
            )
        repos: List[Path] = []
        for child in base.iterdir():
            if not child.is_dir():
                continue
            if (child / ".git").is_dir():
                repos.append(child)
        return sorted(repos)
