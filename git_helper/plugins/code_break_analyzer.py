"""CodeBreakAnalyzer plug-in for regression detection."""

from __future__ import annotations

from typing import Any

from .base import Plugin

from ..diagnostics import DiagnosticEngine

__all__ = ["register"]


def register(git=None) -> Plugin:
    def run(git_interface, app: Any) -> str:
        engine = DiagnosticEngine(git_interface)
        summary = engine.find_breaking_commit()
        commit = None
        if "identified as the first bad commit" in summary:
            commit = summary.split()[0]
        if commit:
            report = engine.generate_report(commit, summary)
            message = f"🚨 CodeBreakAnalyzer\n{summary}\nReport: {report}"
        else:
            message = f"🚨 CodeBreakAnalyzer\n{summary}"
        if hasattr(app, "show_popup") and callable(app.show_popup):
            app.show_popup("CodeBreakAnalyzer", message)
        return message

    return Plugin(
        name="CodeBreakAnalyzer",
        description="Finds which commit introduced app-breaking changes.",
        run=run,
    )

