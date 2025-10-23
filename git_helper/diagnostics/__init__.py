"""Runtime diagnostics and regression detection utilities."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Optional

from ..git_core import GitCore, GitCommandError
from .analyzer import DiffAnalyzer, DiffSummary
from .query_engine import Query, QueryEngine
from .report_builder import ReportBuilder

REPORT_DIR = Path.home() / ".githelper" / "reports"

__all__ = [
    "DiagnosticEngine",
    "DiffAnalyzer",
    "DiffSummary",
    "Query",
    "QueryEngine",
    "ReportBuilder",
]


class DiagnosticEngine:
    """Analyse repository state and discover breaking commits."""

    def __init__(self, git: GitCore) -> None:
        self.git = git
        REPORT_DIR.mkdir(parents=True, exist_ok=True)

    def find_breaking_commit(
        self,
        *,
        known_good: Optional[str] = None,
        known_bad: str = "HEAD",
        test_command: Optional[str] = None,
    ) -> str:
        """Use ``git bisect`` to locate the first bad commit."""

        self.git.ensure_repository()
        subprocess.run(["git", "bisect", "reset"], cwd=self.git.path, check=False)
        start_cmd = ["git", "bisect", "start", known_bad]
        if known_good:
            start_cmd.append(known_good)
        try:
            subprocess.run(start_cmd, cwd=self.git.path, check=True, capture_output=True, text=True)
            subprocess.run(["git", "bisect", "bad", known_bad], cwd=self.git.path, check=True,
                           capture_output=True, text=True)
            if known_good:
                subprocess.run(
                    ["git", "bisect", "good", known_good],
                    cwd=self.git.path,
                    check=True,
                    capture_output=True,
                    text=True,
                )
        except subprocess.CalledProcessError as exc:
            raise GitCommandError(exc.stderr.strip() or exc.stdout.strip() or str(exc)) from exc

        try:
            if known_good:
                pass
            run_command = ["git", "bisect", "run"]
            if test_command:
                run_command.extend(["bash", "-lc", test_command])
            else:
                if shutil.which("pytest"):
                    run_command.append("pytest")
                else:
                    run_command.extend(["python", "-m", "pytest"])
            run_result = subprocess.run(
                run_command,
                cwd=self.git.path,
                capture_output=True,
                text=True,
            )
            output = run_result.stdout + run_result.stderr
            bad_commit = self._parse_first_bad(output)
            if not bad_commit:
                bad_commit = self._current_bisect_commit()
            if bad_commit:
                return f"{bad_commit} identified as the first bad commit."
            return "Unable to determine the first bad commit. Review bisect output manually."
        finally:
            subprocess.run(["git", "bisect", "reset"], cwd=self.git.path, check=False)

    def _current_bisect_commit(self) -> Optional[str]:
        result = subprocess.run(
            ["git", "bisect", "visualize", "--oneline"],
            cwd=self.git.path,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return None
        for line in result.stdout.splitlines():
            parts = line.strip().split()
            if parts:
                return parts[0]
        return None

    def _parse_first_bad(self, output: str) -> Optional[str]:
        for line in output.splitlines():
            if "is the first bad commit" in line:
                return line.split()[0]
        return None

    def summarize_diff(self, commit_hash: str) -> str:
        self.git.ensure_repository()
        result = subprocess.run(
            ["git", "show", commit_hash, "--stat", "--patch"],
            cwd=self.git.path,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise GitCommandError(result.stderr.strip() or result.stdout.strip() or "Unable to summarize diff.")
        return result.stdout

    def generate_report(self, commit_hash: str, summary: str, *, format: str = "markdown") -> Path:
        diff_text = self.summarize_diff(commit_hash)
        if format == "html":
            content = self._html_report(commit_hash, summary, diff_text)
            extension = ".html"
        else:
            content = self._markdown_report(commit_hash, summary, diff_text)
            extension = ".md"
        path = REPORT_DIR / f"diagnostic_{commit_hash}{extension}"
        path.write_text(content, encoding="utf-8")
        return path

    def _markdown_report(self, commit: str, summary: str, diff: str) -> str:
        return f"""# Diagnostic Report for {commit}

**Summary:** {summary}

```diff
{diff[:5000]}
```
"""

    def _html_report(self, commit: str, summary: str, diff: str) -> str:
        escaped = diff[:5000].replace("<", "&lt;").replace(">", "&gt;")
        return f"""<html><body>
<h1>Diagnostic Report for {commit}</h1>
<p><strong>Summary:</strong> {summary}</p>
<pre style=\"background:#111;color:#0f0;padding:1em;\">{escaped}</pre>
</body></html>
"""

