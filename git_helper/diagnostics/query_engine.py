"""Natural language query interpretation for diff analysis."""

from __future__ import annotations

import re
from dataclasses import dataclass

__all__ = ["QueryEngine", "Query"]


@dataclass
class Query:
    type: str
    target: str | list[str] | None


class QueryEngine:
    """Parse human friendly requests into structured search instructions."""

    def parse(self, text: str) -> Query:
        clean = text.lower().strip()
        if not clean:
            return Query(type="text", target=None)
        if "function" in clean:
            matches = re.findall(r"function\s+([\w\.]+)", clean)
            return Query(type="function", target=matches or None)
        if "commit" in clean:
            matches = re.findall(r"commit\s+([a-f0-9]{5,40})", clean)
            return Query(type="commit", target=matches or None)
        if "file" in clean or ".py" in clean:
            matches = re.findall(r"([\w/]+\.\w+)", clean)
            return Query(type="file", target=matches or None)
        return Query(type="text", target=text)

    def describe(self, query: Query) -> str:
        if query.type == "function" and query.target:
            return f"Functions: {', '.join(query.target)}"
        if query.type == "commit" and query.target:
            return f"Commits: {', '.join(query.target)}"
        if query.type == "file" and query.target:
            return f"Files: {', '.join(query.target)}"
        if isinstance(query.target, str):
            return query.target
        return "General diff overview"

