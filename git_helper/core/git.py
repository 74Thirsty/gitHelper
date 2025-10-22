"""Local Git automation helpers."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

from ..errors import GitHelperError
from ..utils.logger import get_logger

__all__ = ["GitStatus", "GitService"]

LOGGER = get_logger(__name__)


class GitServiceError(GitHelperError):
    """Raised when a Git command cannot be executed."""


@dataclass(slots=True)
class GitStatus:
    """Summary of the working tree state."""

    branch: str
    detached: bool
    ahead: int
    behind: int
    staged: int
    unstaged: int
    untracked: int
    stashes: int

    @property
    def clean(self) -> bool:
        """Return True when the working tree is clean."""

        return (
            not self.staged
            and not self.unstaged
            and not self.untracked
            and not self.stashes
        )


class GitService:
    """Execute Git commands and provide higher level workflows."""

    def __init__(self, repo: Path | str | None = None) -> None:
        self.repo_path = Path(repo or Path.cwd()).resolve()

    # ------------------------------------------------------------------ utilities
    def _run(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        command = ["git", *args]
        LOGGER.debug("Running git command", extra={"args": command, "cwd": str(self.repo_path)})
        try:
            result = subprocess.run(
                command,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=check,
            )
        except FileNotFoundError as exc:  # pragma: no cover - git should exist
            raise GitServiceError("Git executable not available") from exc
        except subprocess.CalledProcessError as exc:
            LOGGER.error("Git command failed", extra={"args": command, "stderr": exc.stderr})
            if check:
                raise GitServiceError(exc.stderr.strip()) from exc
            result = exc
        return result

    # ------------------------------------------------------------------- inspection
    def status(self) -> GitStatus:
        """Return a structured summary of ``git status``."""

        result = self._run("status", "--porcelain=v2", "--branch")
        branch = "unknown"
        ahead = behind = 0
        detached = False
        staged = unstaged = untracked = 0
        for line in result.stdout.splitlines():
            if line.startswith("# branch.head "):
                branch = line.split(" ", 2)[2]
                detached = branch == "(detached)"
            elif line.startswith("# branch.ab "):
                parts = line.split()
                ahead = int(parts[2].lstrip("+"))
                behind = int(parts[3].lstrip("-"))
            elif line.startswith("1 "):
                _, codes, *_ = line.split(maxsplit=3)
                x, y = codes[0], codes[1]
                if x != ".":
                    staged += 1
                if y != ".":
                    unstaged += 1
            elif line.startswith("2 "):
                _, codes, *_ = line.split(maxsplit=3)
                x, y = codes[0], codes[1]
                if x != ".":
                    staged += 1
                if y != ".":
                    unstaged += 1
            elif line.startswith("? "):
                untracked += 1
            elif line.startswith("u "):
                staged += 1
                unstaged += 1
            elif line.startswith("# "):
                continue
            else:
                unstaged += 1
        stashes = len(self.list_stashes())
        return GitStatus(
            branch=branch,
            detached=detached,
            ahead=ahead,
            behind=behind,
            staged=staged,
            unstaged=unstaged,
            untracked=untracked,
            stashes=stashes,
        )

    def list_branches(self) -> list[str]:
        """Return local branches."""

        result = self._run("branch", "--format=%(refname:short)")
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]

    def list_remotes(self) -> list[str]:
        result = self._run("remote")
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]

    def list_stashes(self) -> list[str]:
        result = self._run("stash", "list", check=False)
        output = result.stdout.strip()
        if not output:
            return []
        return [line for line in output.splitlines() if line]

    def diff_stat(self, cached: bool = False) -> str:
        args: list[str] = ["diff", "--stat"]
        if cached:
            args.insert(1, "--cached")
        result = self._run(*args)
        return result.stdout.strip()

    def pending_commits(self) -> List[str]:
        result = self._run("log", "--oneline", "origin/HEAD..HEAD", check=False)
        return [line for line in result.stdout.splitlines() if line.strip()]

    def push_branch(self, branch: str, remote: str = "origin", force: bool = False) -> subprocess.CompletedProcess[str]:
        args: list[str] = ["push", remote, branch]
        if force:
            args.append("--force-with-lease")
        return self._run(*args, check=False)

    def fetch(self, remote: str = "origin") -> None:
        self._run("fetch", remote)

    def branches_with_upstream(self) -> list[str]:
        result = self._run("for-each-ref", "--format=%(refname:short) %(upstream)", "refs/heads")
        branches: list[str] = []
        for line in result.stdout.splitlines():
            name, _, upstream = line.partition(" ")
            branches.append(f"{name} -> {upstream.strip()}" if upstream.strip() else name)
        return branches

    # ------------------------------------------------------------- smart commands
    def auto_push_all(self, remote: str = "origin", force: bool = False) -> list[subprocess.CompletedProcess[str]]:
        results: list[subprocess.CompletedProcess[str]] = []
        for branch in self.list_branches():
            LOGGER.info("Pushing branch", extra={"branch": branch, "remote": remote})
            results.append(self.push_branch(branch, remote=remote, force=force))
        return results

    def scan(self) -> dict[str, object]:
        status = self.status()
        return {
            "status": status,
            "branches": self.list_branches(),
            "remotes": self.list_remotes(),
            "stashes": self.list_stashes(),
            "pending_commits": self.pending_commits(),
        }

    def summarize_changes(self) -> str:
        staged = self.diff_stat(cached=True)
        unstaged = self.diff_stat(cached=False)
        sections: list[str] = []
        if staged:
            sections.append("Staged changes:\n" + staged)
        if unstaged:
            sections.append("Unstaged changes:\n" + unstaged)
        if not sections:
            return "No changes detected."
        return "\n\n".join(sections)

    def recommend_resolution_actions(self) -> list[str]:
        status = self.status()
        recommendations: list[str] = []
        if status.untracked:
            recommendations.append("Add or clean up untracked files with 'git add' or 'git clean'.")
        if status.staged and status.unstaged:
            recommendations.append("Consider committing staged changes before addressing unstaged edits.")
        elif status.staged:
            recommendations.append("Commit staged changes.")
        if status.unstaged:
            recommendations.append("Stage or stash unstaged edits before switching branches.")
        if status.stashes:
            recommendations.append("Review stashes with 'git stash list' and apply or drop old entries.")
        if status.ahead:
            recommendations.append("Push local commits to share your work.")
        if status.behind:
            recommendations.append("Pull or fetch and rebase to incorporate remote changes.")
        if not recommendations:
            recommendations.append("Working tree is clean — nothing to resolve!")
        return recommendations

    def recent_log(self, limit: int = 5) -> str:
        result = self._run("log", f"-{limit}", "--decorate", "--graph", "--oneline")
        return result.stdout

    def format_devlog(self, limit: int = 5, github_events: Iterable[str] | None = None) -> str:
        events = "\n".join(github_events or [])
        if events:
            events = "GitHub events:\n" + events + "\n"
        return f"Recent Git commits:\n{self.recent_log(limit)}\n{events}"
