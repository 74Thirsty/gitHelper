"""High level helpers for interacting with Git repositories."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import List, Sequence

__all__ = [
    "GitRepository",
    "GitRepositoryError",
]


class GitRepositoryError(RuntimeError):
    """Raised when an underlying Git command fails."""


class GitRepository:
    """Small convenience wrapper around ``git`` commands.

    The helper focuses on the handful of operations needed by the interactive
    CLI.  It keeps the implementation lightweight while still surfacing useful
    error information when Git is misconfigured or unavailable.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path).expanduser()

    # ----------------------------------------------------------------- helpers
    def _ensure_directory(self) -> None:
        try:
            self.path.mkdir(parents=True, exist_ok=True)
        except OSError as exc:  # pragma: no cover - platform specific
            raise GitRepositoryError(f"Unable to create directory {self.path}: {exc}")

    def _ensure_repository(self) -> None:
        if not self.is_repository:
            raise GitRepositoryError(
                f"{self.path} is not an initialised Git repository. Run git init first."
            )

    def _run(self, *args: str, check: bool = True) -> subprocess.CompletedProcess:
        command: Sequence[str] = ("git", *args)
        try:
            result = subprocess.run(
                command,
                cwd=self.path,
                text=True,
                capture_output=True,
            )
        except FileNotFoundError as exc:
            raise GitRepositoryError("The 'git' executable is not available on PATH.") from exc

        if check and result.returncode != 0:
            message = result.stderr.strip() or result.stdout.strip()
            if not message:
                message = f"git {' '.join(args)} failed with exit code {result.returncode}"
            raise GitRepositoryError(message)
        return result

    # ------------------------------------------------------------------- status
    @property
    def exists(self) -> bool:
        return self.path.exists()

    @property
    def is_repository(self) -> bool:
        return (self.path / ".git").is_dir()

    def status(self) -> str:
        """Return ``git status`` output for the repository."""

        self._ensure_repository()
        result = self._run("status", "--short", "--branch")
        output = result.stdout.strip()
        return output or "Nothing to commit, working tree clean."

    # ------------------------------------------------------------------ actions
    def init(self, *, default_branch: str | None = None) -> str:
        """Initialise a repository at the configured path."""

        self._ensure_directory()
        args = ["init"]
        if default_branch:
            args.extend(["--initial-branch", default_branch])
        result = self._run(*args)
        return result.stdout.strip() or result.stderr.strip()

    def stage_all(self) -> None:
        """Stage all tracked and untracked changes."""

        self._ensure_repository()
        self._run("add", "--all")

    def commit(self, message: str) -> str:
        """Create a commit with *message* and return Git's response."""

        self._ensure_repository()
        if not message.strip():
            raise GitRepositoryError("A commit message is required.")
        result = self._run("commit", "-m", message)
        return result.stdout.strip() or result.stderr.strip()

    def current_branch(self) -> str | None:
        """Return the current branch name or ``None`` when detached."""

        self._ensure_repository()
        result = self._run("rev-parse", "--abbrev-ref", "HEAD")
        branch = result.stdout.strip()
        return None if branch == "HEAD" else branch

    def tracking_branch(self) -> str | None:
        """Return the upstream tracking branch if configured."""

        self._ensure_repository()
        result = self._run(
            "rev-parse",
            "--abbrev-ref",
            "--symbolic-full-name",
            "@{u}",
            check=False,
        )
        if result.returncode != 0:
            return None
        value = result.stdout.strip()
        return value or None

    def push(self, remote: str, branch: str, *, set_upstream: bool = False) -> str:
        """Push the current branch to *remote* and return Git's output."""

        self._ensure_repository()
        args = ["push"]
        if set_upstream:
            args.append("--set-upstream")
        args.extend([remote, branch])
        result = self._run(*args)
        return result.stdout.strip() or result.stderr.strip()

    def pull(self, remote: str, branch: str) -> str:
        """Pull the given *branch* from *remote* and return Git's output."""

        self._ensure_repository()
        result = self._run("pull", remote, branch)
        return result.stdout.strip() or result.stderr.strip()

    def remotes(self) -> List[str]:
        """Return a list of configured remote names."""

        self._ensure_repository()
        result = self._run("remote")
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]

    def remote_exists(self, name: str) -> bool:
        return name in self.remotes()

    def set_remote(self, name: str, url: str, *, replace: bool = False) -> str:
        """Add or update a remote."""

        self._ensure_repository()
        if not url.strip():
            raise GitRepositoryError("A remote URL is required.")
        if self.remote_exists(name):
            if not replace:
                raise GitRepositoryError(
                    f"Remote '{name}' already exists. Enable replace=True to update it."
                )
            result = self._run("remote", "set-url", name, url)
        else:
            result = self._run("remote", "add", name, url)
        return result.stdout.strip() or result.stderr.strip()
