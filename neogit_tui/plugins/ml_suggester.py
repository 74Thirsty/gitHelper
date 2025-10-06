"""Playful commit message suggester plugin."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from ..git import GitInterface
from . import Plugin


FILE_HINTS = {
    ".py": "python", ".sh": "shell", ".md": "docs", ".yml": "config",
    ".yaml": "config", ".json": "config", ".js": "javascript", ".ts": "typescript",
}


def _categorise(paths: list[str]) -> Counter[str]:
    buckets: Counter[str] = Counter()
    for path in paths:
        suffix = Path(path).suffix.lower()
        bucket = FILE_HINTS.get(suffix, "general change")
        buckets[bucket] += 1
    return buckets


def suggest_commit_message(git: GitInterface, _: Any) -> str:
    status_lines = git.status_short()
    if not status_lines:
        return "Working tree is clean – nothing to commit!"
    paths = [line[3:] for line in status_lines if len(line) > 3]
    buckets = _categorise(paths)
    primary = buckets.most_common(2)
    stat = git.diff_stat()
    summary_parts = [f"{count} {name}" for name, count in primary]
    summary = ", ".join(summary_parts) if summary_parts else "assorted updates"
    suggestions = [
        f"chore: polish {summary}",
        f"feat: evolve {primary[0][0]} flow" if primary else "feat: add improvements",
        "refactor: streamline repo per diff stats",
    ]
    report = ["🤖 Commit Message Oracle", "", "Top suggestions:"]
    for idx, idea in enumerate(suggestions, start=1):
        report.append(f"  {idx}. {idea}")
    report.append("")
    report.append("Diff footprint:")
    report.extend([f"  {line}" for line in stat.splitlines()[:10]])
    return "\n".join(report)


def register(git: GitInterface) -> Plugin:  # [REF] accept active GitInterface during plug-in registration
    _ = git  # [REF] explicitly acknowledge interface parameter for clarity and future wiring
    return Plugin(  # [REF] construct plugin instance using canonical dataclass
        name="ML-ish Commit Oracle",  # [REF] expose descriptive plugin label for UI listing
        description="Generate cheeky commit message suggestions based on current diffs.",  # [REF] retain user-facing description text
        run=suggest_commit_message,  # [REF] wire execution callback to suggester routine
    )
