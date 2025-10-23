"""Diff analysis helpers for advanced diagnostics."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from ..git_core import GitCommandError

__all__ = ["DiffAnalyzer", "DiffSummary"]


@dataclass
class DiffSummary:
    files_changed: int
    additions: int
    deletions: int
    preview: str


class DiffAnalyzer:
    """Perform semantic diff analysis for reports and plug-ins."""

    def __init__(self, git_interface) -> None:
        self.git = git_interface

    def get_diff(self, scope: str = "HEAD~1..HEAD") -> str:
        result = subprocess.run(
            ["git", "diff", scope],
            cwd=getattr(self.git, "path", Path.cwd()),
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise GitCommandError(result.stderr.strip() or result.stdout.strip() or "Unable to compute diff.")
        return result.stdout

    def analyze_diff(self, query: Optional[str] = None, scope: str = "HEAD~1..HEAD") -> dict:
        diff = self.get_diff(scope)
        if query:
            filtered = self._filter_by_query(diff, query)
        else:
            filtered = diff
        summary = self._summarize_changes(filtered)
        return {"query": query, "summary": summary}

    def _filter_by_query(self, diff: str, query: str) -> str:
        pattern = re.compile(re.escape(query), re.IGNORECASE)
        return "\n".join(line for line in diff.splitlines() if pattern.search(line))

    def _summarize_changes(self, diff_text: str) -> DiffSummary:
        additions = sum(1 for line in diff_text.splitlines() if line.startswith("+") and not line.startswith("+++"))
        deletions = sum(1 for line in diff_text.splitlines() if line.startswith("-") and not line.startswith("---"))
        files = len(re.findall(r"^diff --git", diff_text, flags=re.MULTILINE))
        preview = diff_text[:2000]
        return DiffSummary(files_changed=files, additions=additions, deletions=deletions, preview=preview)

