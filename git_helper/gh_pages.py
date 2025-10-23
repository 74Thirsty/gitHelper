"""Support utilities for GitHub Pages deployments and Codespaces automation."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Optional

from .git_core import GitCore, GitCommandError, GitRunResult

__all__ = ["GitHubPagesManager"]


@dataclass(slots=True)
class DeploymentResult:
    branch: str
    output: str


class GitHubPagesManager:
    """Automate GitHub Pages deployment flows."""

    def __init__(self, git: GitCore) -> None:
        self.git = git

    def deploy(self, *, branch: str = "gh-pages", build_command: Optional[str] = None,
               force: bool = False) -> DeploymentResult:
        """Deploy the current repository to GitHub Pages."""

        self.git.ensure_repository()
        if build_command:
            self._run_shell(build_command)
        push_branch = branch
        current = self.git.current_branch() or "HEAD"
        if current != branch:
            self.git._run("checkout", branch, check=False)
            self.git._run("checkout", current)
        args = ["push", "origin", f"{current}:{branch}"]
        if force:
            args.insert(1, "--force")
        result = self.git._run(*args)
        return DeploymentResult(branch=branch, output=result.output)

    def open_codespace(self, *, repo: str | None = None) -> str:
        """Launch a GitHub Codespace using the gh CLI."""

        command = ["gh", "codespace", "create"]
        if repo:
            command.extend(["-r", repo])
        try:
            completed = subprocess.run(command, capture_output=True, text=True)
        except FileNotFoundError as exc:  # pragma: no cover - dependency specific
            raise GitCommandError("The GitHub CLI (gh) is required for Codespaces automation.") from exc
        result = GitRunResult(tuple(command), completed.stdout, completed.stderr, completed.returncode)
        if completed.returncode != 0:
            message = result.output or "Failed to launch GitHub Codespace."
            raise GitCommandError(message)
        return result.output

    def _run_shell(self, command: str) -> None:
        try:
            completed = subprocess.run(command, shell=True, cwd=self.git.path, check=True)
        except subprocess.CalledProcessError as exc:  # pragma: no cover - command specific
            raise GitCommandError(f"Build command '{command}' failed: {exc}") from exc

