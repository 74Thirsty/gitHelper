"""Git plumbing helpers for the neon Git cockpit."""

from __future__ import annotations

import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence


class GitCommandError(RuntimeError):
    """Raised when a git command exits unsuccessfully."""

    def __init__(self, command: Sequence[str], returncode: int, stdout: str, stderr: str):
        self.command = list(command)
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        message = stderr.strip() or stdout.strip() or "Unknown git error"
        super().__init__(f"git {' '.join(command)} failed ({returncode}): {message}")


@dataclass
class Commit:
    hash: str
    short_hash: str
    author: str
    date: str
    subject: str


@dataclass
class HeadSnapshot:
    branch: Optional[str]
    commit: str


class GitInterface:
    """A thin convenience wrapper around git commands."""

    def __init__(self, repo_path: Path | str | None = None):
        self.repo_path = Path(repo_path or Path.cwd())
        if not (self.repo_path / ".git").exists():
            raise GitCommandError(["rev-parse"], 128, "", f"Not a git repository: {self.repo_path}")

    # ------------------------------------------------------------------ basics
    def _run(
        self,
        *args: str,
        check: bool = True,
        capture_output: bool = True,
        env: Optional[dict] = None,
    ) -> subprocess.CompletedProcess:
        result = subprocess.run(
            ["git", *args],
            cwd=self.repo_path,
            text=True,
            capture_output=capture_output,
            env={**os.environ, **(env or {})},
        )
        if check and result.returncode != 0:
            raise GitCommandError(args, result.returncode, result.stdout, result.stderr)
        return result

    # ---------------------------------------------------------------- commits
    def list_commits(self, limit: int = 200) -> List[Commit]:
        result = self._run(
            "log",
            f"--max-count={limit}",
            "--date=short",
            "--pretty=format:%H%x09%h%x09%an%x09%ad%x09%s",
        )
        commits: List[Commit] = []
        for line in result.stdout.splitlines():
            if not line.strip():
                continue
            parts = line.split("\t", 4)
            if len(parts) < 5:
                continue
            full, short, author, date, subject = parts
            commits.append(Commit(full, short, author, date, subject))
        return commits

    def get_diff(self, commit_hash: str, context: int = 3) -> str:
        result = self._run("show", commit_hash, f"-U{context}", "--color=never")
        return result.stdout

    # --------------------------------------------------------------- references
    def current_branch(self) -> Optional[str]:
        result = self._run("rev-parse", "--abbrev-ref", "HEAD")
        branch = result.stdout.strip()
        return None if branch == "HEAD" else branch

    def default_branch(self) -> str:
        try:
            result = self._run("symbolic-ref", "refs/remotes/origin/HEAD")
            ref = result.stdout.strip()
            if ref.startswith("refs/remotes/origin/"):
                return ref.split("/")[-1]
        except GitCommandError:
            pass
        for candidate in ("main", "master", "develop"):
            try:
                self._run("rev-parse", f"origin/{candidate}")
                return candidate
            except GitCommandError:
                continue
        return "main"

    def branch_exists(self, branch: str) -> bool:
        try:
            self._run("rev-parse", "--verify", branch)
            return True
        except GitCommandError:
            return False

    def list_branches(self) -> str:
        result = self._run("branch", "--all", "--verbose", "--color=never")
        return result.stdout

    def branch_graph(self) -> str:
        result = self._run("log", "--graph", "--decorate", "--oneline", "--all")
        return result.stdout

    # ----------------------------------------------------------------- actions
    def checkout(self, ref: str) -> None:
        self._run("checkout", ref)

    def create_branch(self, branch: str, commit: str) -> None:
        self._run("branch", branch, commit)

    def switch(self, branch: str) -> None:
        self._run("switch", branch)

    def checkout_temporary_branch(self, commit: Commit) -> str:
        base = f"play/{commit.short_hash}"
        name = base
        counter = 1
        while self.branch_exists(name):
            counter += 1
            name = f"{base}-{counter}"
        self._run("switch", "-c", name, commit.hash)
        return name

    def fast_forward(self, target: Optional[str] = None) -> str:
        branch = target or self.default_branch()
        self._run("fetch", "origin", branch)
        self._run("merge", "--ff-only", f"origin/{branch}")
        return branch

    def merge_preview(self, ref: str) -> str:
        result = self._run("diff", "--stat", f"HEAD...{ref}")
        return result.stdout

    def merge(self, ref: str) -> str:
        result = self._run("merge", ref)
        return result.stdout

    def force_push(self, branch: Optional[str] = None) -> str:
        target = branch or self.current_branch()
        if not target:
            raise GitCommandError(["push"], 1, "", "Cannot force push in detached HEAD state")
        result = self._run("push", "--force-with-lease", "origin", target)
        return result.stdout

    def rollback_hard(self, commit: str) -> None:
        self._run("reset", "--hard", commit)

    def working_tree_is_clean(self) -> bool:
        result = self._run("status", "--porcelain")
        return result.stdout.strip() == ""

    def stash(self) -> str:
        result = self._run("stash")
        return result.stdout

    def status_short(self) -> List[str]:
        result = self._run("status", "--short")
        return [line.rstrip() for line in result.stdout.splitlines()]

    def diff_stat(self, ref: Optional[str] = None) -> str:
        args = ["diff", "--stat"]
        if ref:
            args.append(ref)
        result = self._run(*args)
        return result.stdout

    # ----------------------------------------------------------- undo / redo
    def snapshot_head(self) -> HeadSnapshot:
        branch = self.current_branch()
        commit = self._run("rev-parse", "HEAD").stdout.strip()
        return HeadSnapshot(branch=branch, commit=commit)

    def restore_snapshot(self, snapshot: HeadSnapshot) -> None:
        if snapshot.branch:
            self._run("switch", snapshot.branch)
        else:
            self._run("checkout", snapshot.commit)

    # ------------------------------------------------------------- rebase todo
    def build_rebase_todo(self, count: int) -> List[Commit]:
        result = self._run(
            "log",
            f"--max-count={count}",
            "--pretty=format:%H%x09%h%x09%an%x09%ad%x09%s",
        )
        commits: List[Commit] = []
        for line in result.stdout.splitlines():
            if not line.strip():
                continue
            full, short, author, date, subject = line.split("\t", 4)
            commits.append(Commit(full, short, author, date, subject))
        return commits

    def run_interactive_rebase(self, actions: List[tuple[str, Commit]]) -> None:
        if not actions:
            return
        todo_lines = [f"{action} {commit.hash} {commit.subject}".strip() for action, commit in actions]
        depth = len(actions)
        with tempfile.NamedTemporaryFile("w", delete=False) as tmp:
            tmp.write("\n".join(todo_lines))
            tmp.flush()
            env = {
                "GIT_SEQUENCE_EDITOR": f"cat {tmp.name}",
            }
            self._run("rebase", "-i", f"HEAD~{depth}", env=env)
        os.unlink(tmp.name)

    # ------------------------------------------------------------- repo info
    def remote_url(self) -> Optional[str]:
        try:
            result = self._run("config", "--get", "remote.origin.url")
            return result.stdout.strip() or None
        except GitCommandError:
            return None

    def repo_slug(self) -> Optional[str]:
        url = self.remote_url()
        if not url:
            return None
        cleaned = url
        if cleaned.endswith(".git"):
            cleaned = cleaned[:-4]
        if cleaned.startswith("git@"):
            cleaned = cleaned.replace(":", "/", 1)
            cleaned = cleaned.split("@", 1)[-1]
        if cleaned.startswith("https://") or cleaned.startswith("http://"):
            cleaned = cleaned.split("//", 1)[-1]
        parts = cleaned.split("/")
        if len(parts) >= 2:
            owner = parts[-2]
            name = parts[-1]
            return f"{owner}/{name}"
        return None
