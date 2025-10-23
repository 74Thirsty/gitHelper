"""GUI settings persistence for gitHelper."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable

SETTINGS_DIR = Path.home() / ".config" / "git_helper"
SETTINGS_FILE = SETTINGS_DIR / "settings.json"
DEFAULT_SETTINGS: Dict[str, Any] = {
    "theme": "system",
    "disabled_plugins": [],
    "window": {"width": 1280, "height": 720},
}

__all__ = ["SettingsManager", "SETTINGS_FILE", "DEFAULT_SETTINGS"]


@dataclass
class SettingsManager:
    """Load and persist GUI-specific preferences."""

    path: Path = field(default=SETTINGS_FILE)
    data: Dict[str, Any] = field(default_factory=lambda: DEFAULT_SETTINGS.copy())

    def __post_init__(self) -> None:
        self.path = Path(self.path)
        self.reload()

    def reload(self) -> None:
        if not self.path.exists():
            self.save()
            return
        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            self.data = DEFAULT_SETTINGS.copy()
            self.save()
            return
        merged = DEFAULT_SETTINGS.copy()
        if isinstance(loaded, dict):
            merged.update(loaded)
        merged.setdefault("disabled_plugins", [])
        self.data = merged

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        content = json.dumps(self.data, indent=2, sort_keys=True)
        self.path.write_text(content, encoding="utf-8")

    # ---------------------------------------------------------------- utilities
    def get(self, key: str, default: Any | None = None) -> Any:
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.data[key] = value
        self.save()

    def disable_plugin(self, name: str) -> None:
        disabled = set(self.data.get("disabled_plugins", []))
        disabled.add(name)
        self.data["disabled_plugins"] = sorted(disabled)
        self.save()

    def enable_plugin(self, name: str) -> None:
        disabled = set(self.data.get("disabled_plugins", []))
        if name in disabled:
            disabled.remove(name)
            self.data["disabled_plugins"] = sorted(disabled)
            self.save()

    def is_plugin_enabled(self, name: str) -> bool:
        disabled = set(self.data.get("disabled_plugins", []))
        return name not in disabled

    def disabled_plugins(self) -> Iterable[str]:
        return tuple(self.data.get("disabled_plugins", []))

