"""DiffSummarizer Bot plug-in entry point."""

from __future__ import annotations

import os
from typing import Any

from neogit_tui.plugins import Plugin

from ..diagnostics import DiffAnalyzer, ReportBuilder
from ..diagnostics.query_engine import QueryEngine

__all__ = ["register"]


def _prompt(app: Any, message: str) -> str:
    if app is None:
        return ""
    prompt = getattr(app, "prompt", None)
    if callable(prompt):
        return prompt(message)
    return getattr(app, "default_query", "")


def _notify(app: Any, title: str, body: str) -> None:
    popup = getattr(app, "show_popup", None)
    if callable(popup):
        popup(title, body)


def _ai_summary(diff_text: str) -> str | None:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        from openai import OpenAI  # type: ignore
    except Exception:  # pragma: no cover - optional dependency
        return None
    try:
        client = OpenAI(api_key=api_key)
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": f"Summarize the following git diff in concise bullet points:\n{diff_text[:4000]}",
                }
            ],
        )
        return completion.choices[0].message.content or None
    except Exception:  # pragma: no cover - external service errors
        return None


def register(git=None) -> Plugin:
    query_engine = QueryEngine()

    def run(git_interface, app) -> str:
        analyzer = DiffAnalyzer(git_interface)
        query_text = _prompt(app, "Enter a topic or file/function to summarize:")
        query = query_engine.parse(query_text)
        results = analyzer.analyze_diff(query_text)
        results.setdefault("query_description", query_engine.describe(query))
        analysis_summary = results["summary"]
        report = ReportBuilder(results)
        report_path = report.persist(format="markdown")
        ai_text = _ai_summary(analysis_summary.preview if hasattr(analysis_summary, "preview") else str(analysis_summary))
        if ai_text:
            results["ai_summary"] = ai_text
        message_lines = [
            "Diff summary generated.",
            f"Query: {results['query_description']}",
            f"Files changed: {getattr(analysis_summary, 'files_changed', 0)}",
            f"Additions: {getattr(analysis_summary, 'additions', 0)}",
            f"Deletions: {getattr(analysis_summary, 'deletions', 0)}",
            f"Report saved to: {report_path}",
        ]
        if ai_text:
            message_lines.append("AI summary available in report metadata.")
        _notify(app, "Diff Summary Generated", "\n".join(message_lines))
        return "\n".join(message_lines)

    return Plugin(
        name="DiffSummarizer Bot",
        description="AI-powered diff and report generator for targeted queries.",
        run=run,
    )

