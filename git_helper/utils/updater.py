"""Auto-update helper using the GitHub Releases API."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Optional
from urllib.error import URLError
from urllib.request import Request, urlopen

GITHUB_REPO = "cahirsch/gitHelper"
API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

__all__ = ["ReleaseInfo", "check_for_update"]


@dataclass
class ReleaseInfo:
    tag_name: str
    html_url: str
    body: str


def _fetch_latest_release() -> Optional[ReleaseInfo]:
    request = Request(API_URL, headers={"Accept": "application/vnd.github+json"})
    try:
        with urlopen(request, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (URLError, TimeoutError, json.JSONDecodeError):  # pragma: no cover - network dependent
        return None
    tag = payload.get("tag_name")
    url = payload.get("html_url")
    body = payload.get("body", "")
    if not (tag and url):
        return None
    return ReleaseInfo(tag_name=tag, html_url=url, body=body)


def check_for_update(current_version: str) -> Optional[ReleaseInfo]:
    """Return release info when a newer version is available."""

    latest = _fetch_latest_release()
    if not latest:
        return None
    def normalize(tag: str) -> str:
        return tag.lstrip("v")
    if normalize(latest.tag_name) == normalize(current_version):
        return None
    return latest

