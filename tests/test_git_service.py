from __future__ import annotations

import subprocess
from pathlib import Path

from git_helper.core.git import GitService


def run_git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


def test_git_status_counts(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    run_git(repo, "init")
    run_git(repo, "config", "user.name", "Tester")
    run_git(repo, "config", "user.email", "tester@example.com")
    (repo / "tracked.txt").write_text("hello\n")
    run_git(repo, "add", "tracked.txt")
    run_git(repo, "commit", "-m", "initial commit")

    # create stash entry
    (repo / "temp.txt").write_text("stash me")
    run_git(repo, "add", "temp.txt")
    run_git(repo, "stash", "push", "-m", "temp stash")

    # staged file
    (repo / "staged.txt").write_text("staged")
    run_git(repo, "add", "staged.txt")

    # unstaged modification
    (repo / "tracked.txt").write_text("hello world\n")

    # untracked file
    (repo / "notes.md").write_text("todo")

    service = GitService(repo)
    status = service.status()
    assert status.staged >= 1
    assert status.unstaged >= 1
    assert status.untracked >= 1
    assert status.stashes == 1
    assert status.branch in {"main", "master"}
    assert not status.detached
    assert status.clean is False

    summary = service.summarize_changes()
    assert "staged.txt" in summary or "1 file changed" in summary
    recommendations = service.recommend_resolution_actions()
    assert recommendations
