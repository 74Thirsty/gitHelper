"""Diff analyzer utilities used throughout the gitHelper GUI."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Dict, Iterable


@dataclass(frozen=True)
class DiffSummary:
    """Structured summary of a unified diff."""

    total_changes: int
    additions: Dict[str, int]
    deletions: Dict[str, int]

    def as_lines(self) -> Iterable[str]:
        """Render the summary as human readable lines."""

        yield f"Total changes detected: {self.total_changes}"
        if self.additions:
            yield "Top additions:"
            for line, count in sorted(self.additions.items(), key=lambda item: (-item[1], item[0])):
                yield f"  + {line} ({count}×)"
        if self.deletions:
            yield "Top deletions:"
            for line, count in sorted(self.deletions.items(), key=lambda item: (-item[1], item[0])):
                yield f"  - {line} ({count}×)"


class DiffAnalyzer:
    """Utility class that extracts quick insights from git diffs."""

    def summarize(self, diff_text: str) -> DiffSummary:
        additions: Counter[str] = Counter()
        deletions: Counter[str] = Counter()

        for block in diff_text.split("\n@@"):
            if "@@" not in block:
                continue
            _, _, content = block.partition("@@")
            for line in content.splitlines():
                if line.startswith("+++ ") or line.startswith("--- "):
                    continue
                if line.startswith("+"):
                    additions[line[1:].lstrip()] += 1
                elif line.startswith("-"):
                    deletions[line[1:].lstrip()] += 1

        total_changes = sum(additions.values()) + sum(deletions.values())
        return DiffSummary(total_changes=total_changes, additions=dict(additions), deletions=dict(deletions))


__all__ = ["DiffAnalyzer", "DiffSummary"]
