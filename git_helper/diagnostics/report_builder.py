"""Report formatters for diagnostics output."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

__all__ = ["ReportBuilder"]

REPORT_OUTPUT_DIR = Path.home() / ".githelper" / "reports"
REPORT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class ReportBuilder:
    analysis: Dict[str, object]

    def render_markdown(self) -> str:
        summary = self.analysis.get("summary", {})
        files_changed = getattr(summary, "files_changed", None) or summary.get("files_changed", 0)
        additions = getattr(summary, "additions", None) or summary.get("additions", 0)
        deletions = getattr(summary, "deletions", None) or summary.get("deletions", 0)
        preview = getattr(summary, "preview", None) or summary.get("preview", "")
        query = self.analysis.get("query")
        return f"""# Diff Report — {time.ctime()}

**Query:** `{query or 'latest changes'}`  
**Files Changed:** {files_changed}  
**Additions:** {additions}  
**Deletions:** {deletions}

---

### 🔍 Diff Preview
```diff
{preview}
```
"""

    def render_html(self) -> str:
        summary = self.analysis.get("summary", {})
        files_changed = getattr(summary, "files_changed", None) or summary.get("files_changed", 0)
        additions = getattr(summary, "additions", None) or summary.get("additions", 0)
        deletions = getattr(summary, "deletions", None) or summary.get("deletions", 0)
        preview = getattr(summary, "preview", None) or summary.get("preview", "")
        escaped = preview.replace("<", "&lt;").replace(">", "&gt;")
        query = self.analysis.get("query") or "latest changes"
        return f"""
<html><body>
<h2>Diff Report — {time.ctime()}</h2>
<p><b>Query:</b> {query}</p>
<p><b>Files Changed:</b> {files_changed}</p>
<p><b>Additions:</b> {additions}</p>
<p><b>Deletions:</b> {deletions}</p>
<pre style="background:#111;color:#0f0;padding:1em;">{escaped}</pre>
</body></html>
"""

    def persist(self, *, format: str = "markdown") -> Path:
        content = self.render_markdown() if format == "markdown" else self.render_html()
        extension = ".md" if format == "markdown" else ".html"
        output_dir = REPORT_OUTPUT_DIR
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"diff_report_{int(time.time())}{extension}"
        path.write_text(content, encoding="utf-8")
        return path

