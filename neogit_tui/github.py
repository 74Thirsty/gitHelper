"""GitHub integrations for the neon Git cockpit."""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from typing import Dict, List, Optional

from .git import GitInterface


class GitHubUnavailable(RuntimeError):
    """Raised when GitHub features cannot be used."""


@dataclass
class GitHubItem:
    number: int
    title: str
    state: str
    url: str
    author: str
    updated_at: str
    type: str


@dataclass
class WorkflowRun:
    name: str
    status: str
    conclusion: Optional[str]
    url: str
    created_at: str


class GitHubClient:
    """Thin wrapper around the GitHub CLI (gh)."""

    def __init__(self, git: GitInterface):
        if shutil.which("gh") is None:
            raise GitHubUnavailable("GitHub CLI (gh) is not installed.")
        self.git = git
        slug = git.repo_slug()
        if not slug:
            raise GitHubUnavailable("Cannot resolve repository slug from git remotes.")
        self.slug = slug

    # ---------------------------------------------------------------- utilities
    def _run(self, *args: str) -> subprocess.CompletedProcess:
        result = subprocess.run(
            ["gh", *args],
            text=True,
            capture_output=True,
        )
        if result.returncode != 0:
            raise GitHubUnavailable(result.stderr.strip() or result.stdout.strip())
        return result

    def _api_json(self, endpoint: str, params: Optional[Dict[str, str]] = None) -> object:
        command = ["api", endpoint]
        params = params or {}
        for key, value in params.items():
            command.extend(["-f", f"{key}={value}"])
        result = self._run(*command)
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise GitHubUnavailable(f"Failed to parse GitHub response: {exc}") from exc

    # -------------------------------------------------------------------- issues
    def list_issues(self, state: str = "open", limit: int = 20) -> List[GitHubItem]:
        data = self._api_json(
            f"repos/{self.slug}/issues",
            {"state": state, "per_page": str(limit)},
        )
        items: List[GitHubItem] = []
        for entry in data:
            if "pull_request" in entry:
                # The issues endpoint returns PRs as well; skip them here.
                continue
            items.append(
                GitHubItem(
                    number=entry["number"],
                    title=entry["title"],
                    state=entry["state"],
                    url=entry.get("html_url", ""),
                    author=entry.get("user", {}).get("login", "unknown"),
                    updated_at=entry.get("updated_at", ""),
                    type="issue",
                )
            )
        return items

    # ------------------------------------------------------------------------ PRs
    def list_pull_requests(self, state: str = "open", limit: int = 20) -> List[GitHubItem]:
        data = self._api_json(
            f"repos/{self.slug}/pulls",
            {"state": state, "per_page": str(limit)},
        )
        items: List[GitHubItem] = []
        for entry in data:
            items.append(
                GitHubItem(
                    number=entry["number"],
                    title=entry["title"],
                    state=entry["state"],
                    url=entry.get("html_url", ""),
                    author=entry.get("user", {}).get("login", "unknown"),
                    updated_at=entry.get("updated_at", ""),
                    type="pull",
                )
            )
        return items

    # --------------------------------------------------------------- workflow runs
    def list_workflows(self, limit: int = 10) -> List[WorkflowRun]:
        data = self._api_json(
            f"repos/{self.slug}/actions/runs",
            {"per_page": str(limit)},
        )
        runs: List[WorkflowRun] = []
        for entry in data.get("workflow_runs", []):
            runs.append(
                WorkflowRun(
                    name=entry.get("name", entry.get("display_title", "workflow")),
                    status=entry.get("status", "unknown"),
                    conclusion=entry.get("conclusion"),
                    url=entry.get("html_url", ""),
                    created_at=entry.get("created_at", ""),
                )
            )
        return runs

    # ------------------------------------------------------------------- searching
    def lookup_issue_or_pr(self, number: int) -> GitHubItem:
        data = self._api_json(f"repos/{self.slug}/issues/{number}")
        item_type = "pull" if "pull_request" in data else "issue"
        return GitHubItem(
            number=data["number"],
            title=data["title"],
            state=data["state"],
            url=data.get("html_url", ""),
            author=data.get("user", {}).get("login", "unknown"),
            updated_at=data.get("updated_at", ""),
            type=item_type,
        )

    def merge_pull_request(self, number: int, method: str = "merge") -> str:
        if method not in {"merge", "squash", "rebase"}:
            method = "merge"
        flag = f"--{method}"
        result = self._run("pr", "merge", str(number), flag, "--repo", self.slug, "--auto")
        return result.stdout.strip()

    def comment(self, number: int, body: str) -> str:
        result = self._run(
            "api",
            f"repos/{self.slug}/issues/{number}/comments",
            "-X",
            "POST",
            "-f",
            f"body={body}",
        )
        return result.stdout.strip()


def try_create_client(git: GitInterface) -> GitHubClient | None:
    try:
        return GitHubClient(git)
    except GitHubUnavailable:
        return None
