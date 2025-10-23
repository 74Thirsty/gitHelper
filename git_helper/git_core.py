"""High level Git workflow façade used by CLI and GUI frontends."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

from .git import GitRepository, GitRepositoryError

__all__ = ["GitCore", "GitCommandError"]


class GitCommandError(RuntimeError):
    """Raised when an underlying git command fails."""


@dataclass(slots=True)
class GitRunResult:
    """A lightweight view of a git command execution."""

    command: tuple[str, ...]
    stdout: str
    stderr: str
    returncode: int

    @property
    def output(self) -> str:
        text = self.stdout.strip() or self.stderr.strip()
        return text or "".join(self.command)


class GitCore:
    """Expose high level git operations for UI layers."""

    def __init__(self, path: str | Path) -> None:
        self.repository = GitRepository(path)
        self.path = self.repository.path

    # ------------------------------------------------------------------ helpers
    def _run(self, *args: str, check: bool = True) -> GitRunResult:
        command = ("git", *args)
        try:
            completed = subprocess.run(
                command,
                cwd=self.path,
                text=True,
                capture_output=True,
            )
        except FileNotFoundError as exc:  # pragma: no cover - environment specific
            raise GitCommandError("The 'git' executable is required but was not found.") from exc
        result = GitRunResult(command, completed.stdout, completed.stderr, completed.returncode)
        if check and completed.returncode != 0:
            message = result.output or f"git {' '.join(args)} failed with exit code {completed.returncode}"
            raise GitCommandError(message)
        return result

    # ------------------------------------------------------------------ discovery
    def status(self) -> str:
        return self.repository.status()

    def current_branch(self) -> Optional[str]:
        return self.repository.current_branch()

    def tracking_branch(self) -> Optional[str]:
        return self.repository.tracking_branch()

    def log(self, limit: int = 10) -> str:
        result = self._run("log", f"-{limit}", "--oneline", check=False)
        return result.stdout.strip() or "No commits yet."

    # ---------------------------------------------------------------- operations
    def stage_all(self) -> None:
        self.repository.stage_all()

    def commit(self, message: str) -> str:
        return self.repository.commit(message)

    def push(self, remote: str, branch: str, *, set_upstream: bool = False) -> str:
        return self.repository.push(remote, branch, set_upstream=set_upstream)

    def pull(self, remote: str, branch: str) -> str:
        return self.repository.pull(remote, branch)

    def set_remote(self, name: str, url: str, *, replace: bool = False) -> str:
        return self.repository.set_remote(name, url, replace=replace)

    # --------------------------------------------------------------- repo admin
    @staticmethod
    def clone(url: str, destination: str | Path) -> GitRunResult:
        dest = Path(destination).expanduser()
        try:
            dest.mkdir(parents=True, exist_ok=True)
        except OSError as exc:  # pragma: no cover - OS specific
            raise GitCommandError(f"Unable to create {dest}: {exc}") from exc
        command = ("git", "clone", url, str(dest))
        try:
            completed = subprocess.run(command, text=True, capture_output=True)
        except FileNotFoundError as exc:  # pragma: no cover - environment specific
            raise GitCommandError("The 'git' executable is required but was not found.") from exc
        result = GitRunResult(command, completed.stdout, completed.stderr, completed.returncode)
        if completed.returncode != 0:
            message = result.output or f"git clone failed with exit code {completed.returncode}"
            raise GitCommandError(message)
        return result

    def create_branch(self, name: str, *, checkout: bool = True) -> str:
        if not name.strip():
            raise GitCommandError("Branch name cannot be empty.")
        result = self._run("branch", name)
        if checkout:
            self.checkout(name)
        return result.output

    def checkout(self, target: str) -> str:
        return self._run("checkout", target).output

    def revert(self, commit: str) -> str:
        if not commit:
            raise GitCommandError("A commit hash is required to revert changes.")
        return self._run("revert", commit, "--no-edit").output

    def run_custom(self, args: Iterable[str]) -> GitRunResult:
        args_tuple = tuple(args)
        if not args_tuple:
            raise GitCommandError("No git arguments supplied.")
        return self._run(*args_tuple)

    # --------------------------------------------------------------- utilities
    def ensure_repository(self) -> None:
        try:
            self.repository._ensure_repository()
        except GitRepositoryError as exc:
            raise GitCommandError(str(exc)) from exc

