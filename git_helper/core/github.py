"""GitHub API integration powered by PyGithub."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence

try:  # pragma: no cover - dependency optional in tests
    from github import Github, GithubException
except Exception:  # pragma: no cover - fallback when PyGithub missing
    Github = None  # type: ignore
    GithubException = Exception  # type: ignore

from ..errors import GitHelperError
from ..utils.logger import get_logger

__all__ = ["RepositoryDescriptor", "GitHubService", "GitHubServiceError"]

LOGGER = get_logger(__name__)


class GitHubServiceError(GitHelperError):
    """Raised when a GitHub API call fails."""


@dataclass(slots=True)
class RepositoryDescriptor:
    """Simplified view of a GitHub repository."""

    full_name: str
    private: bool
    default_branch: str
    url: str


class GitHubService:
    """High level GitHub operations built on PyGithub."""

    def __init__(self, token: str) -> None:
        if not token:
            raise GitHubServiceError("A GitHub token is required for API access.")
        if Github is None:
            raise GitHubServiceError(
                "PyGithub is not installed. Add 'PyGithub' to your environment to enable API access."
            )
        self._token = token
        self._client = Github(token, per_page=100)

    # ---------------------------------------------------------------- account info
    def current_user(self) -> str:
        try:
            user = self._client.get_user()
        except GithubException as exc:  # pragma: no cover - network behaviour
            raise GitHubServiceError(str(exc)) from exc
        return user.login

    def accessible_repositories(self) -> List[RepositoryDescriptor]:
        try:
            repos = self._client.get_user().get_repos()
        except GithubException as exc:  # pragma: no cover
            raise GitHubServiceError(str(exc)) from exc
        return [
            RepositoryDescriptor(
                full_name=repo.full_name,
                private=repo.private,
                default_branch=repo.default_branch,
                url=repo.html_url,
            )
            for repo in repos
        ]

    def fetch_repository(self, full_name: str):  # type: ignore[override]
        try:
            return self._client.get_repo(full_name)
        except GithubException as exc:  # pragma: no cover
            raise GitHubServiceError(str(exc)) from exc

    def branches(self, full_name: str) -> List[str]:
        repo = self.fetch_repository(full_name)
        try:
            branches = repo.get_branches()
        except GithubException as exc:  # pragma: no cover
            raise GitHubServiceError(str(exc)) from exc
        return [branch.name for branch in branches]

    def tags(self, full_name: str) -> List[str]:
        repo = self.fetch_repository(full_name)
        try:
            tags = repo.get_tags()
        except GithubException as exc:  # pragma: no cover
            raise GitHubServiceError(str(exc)) from exc
        return [tag.name for tag in tags]

    def create_branch(self, full_name: str, new_branch: str, from_branch: str) -> None:
        repo = self.fetch_repository(full_name)
        source_ref = repo.get_git_ref(f"heads/{from_branch}")
        try:
            repo.create_git_ref(ref=f"refs/heads/{new_branch}", sha=source_ref.object.sha)
        except GithubException as exc:  # pragma: no cover
            raise GitHubServiceError(str(exc)) from exc

    def delete_branch(self, full_name: str, branch: str) -> None:
        repo = self.fetch_repository(full_name)
        try:
            ref = repo.get_git_ref(f"heads/{branch}")
            ref.delete()
        except GithubException as exc:  # pragma: no cover
            raise GitHubServiceError(str(exc)) from exc

    def create_pull_request(
        self,
        full_name: str,
        title: str,
        body: str,
        head: str,
        base: str,
        draft: bool = False,
    ) -> str:
        repo = self.fetch_repository(full_name)
        try:
            pr = repo.create_pull(title=title, body=body, head=head, base=base, draft=draft)
        except GithubException as exc:  # pragma: no cover
            raise GitHubServiceError(str(exc)) from exc
        return pr.html_url

    def merge_pull_request(self, full_name: str, number: int, message: str | None = None) -> None:
        repo = self.fetch_repository(full_name)
        try:
            pr = repo.get_pull(number)
            pr.merge(commit_message=message)
        except GithubException as exc:  # pragma: no cover
            raise GitHubServiceError(str(exc)) from exc

    def close_pull_request(self, full_name: str, number: int) -> None:
        repo = self.fetch_repository(full_name)
        try:
            pr = repo.get_pull(number)
            pr.edit(state="closed")
        except GithubException as exc:  # pragma: no cover
            raise GitHubServiceError(str(exc)) from exc

    def comment_on_pull(self, full_name: str, number: int, body: str) -> None:
        repo = self.fetch_repository(full_name)
        try:
            pr = repo.get_pull(number)
            pr.create_issue_comment(body)
        except GithubException as exc:  # pragma: no cover
            raise GitHubServiceError(str(exc)) from exc

    def manage_issue(
        self,
        full_name: str,
        title: str,
        body: str,
        labels: Sequence[str] | None = None,
        assignees: Sequence[str] | None = None,
    ) -> int:
        repo = self.fetch_repository(full_name)
        try:
            issue = repo.create_issue(title=title, body=body, labels=list(labels or ()), assignees=list(assignees or ()))
        except GithubException as exc:  # pragma: no cover
            raise GitHubServiceError(str(exc)) from exc
        return issue.number

    def search_issues(self, query: str) -> List[str]:
        try:
            results = self._client.search_issues(query=query)
        except GithubException as exc:  # pragma: no cover
            raise GitHubServiceError(str(exc)) from exc
        return [f"#{issue.number} {issue.title} ({issue.state})" for issue in results]

    def update_issue_state(self, full_name: str, number: int, state: str) -> None:
        repo = self.fetch_repository(full_name)
        try:
            issue = repo.get_issue(number)
            issue.edit(state=state)
        except GithubException as exc:  # pragma: no cover
            raise GitHubServiceError(str(exc)) from exc

    def ensure_scopes(self, required_scopes: Sequence[str]) -> List[str]:
        try:
            headers = self._client.get_user().raw_headers
        except GithubException as exc:  # pragma: no cover
            raise GitHubServiceError(str(exc)) from exc
        scopes = {scope.strip() for scope in headers.get("X-OAuth-Scopes", "").split(",") if scope.strip()}
        missing = [scope for scope in required_scopes if scope not in scopes]
        if missing:
            raise GitHubServiceError(
                "Missing required GitHub token scopes: " + ", ".join(missing)
            )
        return sorted(scopes)

    def changelog_from_commits(self, full_name: str, base: str, head: str) -> str:
        repo = self.fetch_repository(full_name)
        try:
            comparison = repo.compare(base, head)
        except GithubException as exc:  # pragma: no cover
            raise GitHubServiceError(str(exc)) from exc
        lines = [f"Changes from {base} to {head}:"]
        for commit in comparison.commits:
            lines.append(f"- {commit.commit.message.splitlines()[0]} ({commit.sha[:7]})")
        return "\n".join(lines)

    def recent_events(self, full_name: str, limit: int = 5) -> List[str]:
        repo = self.fetch_repository(full_name)
        try:
            events = repo.get_events()[:limit]
        except GithubException as exc:  # pragma: no cover
            raise GitHubServiceError(str(exc)) from exc
        return [f"{event.type} by {event.actor.login}" for event in events]
