"""Configuration management for gitHelper."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict

try:  # pragma: no cover
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore

try:  # pragma: no cover
    import tomli_w
except ModuleNotFoundError:  # pragma: no cover
    tomli_w = None  # type: ignore

CONFIG_DIR = Path(os.environ.get("GITHELPER_CONFIG_DIR", Path.home() / ".config" / "githelper"))
CONFIG_FILE = CONFIG_DIR / "config.toml"

__all__ = ["ConfigManager", "CONFIG_DIR", "CONFIG_FILE"]


def _default_config_path() -> Path:
    override = os.environ.get("GITHELPER_CONFIG_DIR")
    if override:
        return Path(override) / "config.toml"
    return CONFIG_FILE


DEFAULT_CONFIG: Dict[str, Any] = {
    "github": {
        "default_org": "",
        "preferred_repos": [],
    },
    "ui": {
        "theme": "system",
        "use_gui": False,
    },
    "editor": {
        "command": os.environ.get("EDITOR", "nano"),
    },
}


@dataclass
class ConfigManager:
    """Load and persist gitHelper configuration in TOML."""

    path: Path = field(default_factory=_default_config_path)
    data: Dict[str, Any] = field(default_factory=lambda: DEFAULT_CONFIG.copy())

    def __post_init__(self) -> None:
        self.path = Path(self.path)
        self.reload()

    # --------------------------------------------------------------------- helpers
    def reload(self) -> None:
        """Load configuration from disk if present."""

        if not self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.data = DEFAULT_CONFIG.copy()
            self.save()
            return
        with self.path.open("rb") as fh:
            loaded = tomllib.load(fh)
        merged = DEFAULT_CONFIG.copy()
        for key, value in loaded.items():
            merged[key] = value
        self.data = merged

    def save(self) -> None:
        """Persist configuration to disk."""

        self.path.parent.mkdir(parents=True, exist_ok=True)
        if tomli_w:
            with self.path.open("wb") as fh:  # pragma: no branch - depends on dependency
                tomli_w.dump(self.data, fh)
        else:  # pragma: no cover - fallback path
            content = _dump_toml(self.data)
            self.path.write_text(content, encoding="utf-8")

    # ----------------------------------------------------------------- convenience
    def get(self, section: str, key: str, default: Any | None = None) -> Any:
        return self.data.get(section, {}).get(key, default)

    def set(self, section: str, key: str, value: Any) -> None:
        self.data.setdefault(section, {})[key] = value
        self.save()

    def profile_summary(self) -> str:
        github = self.data.get("github", {})
        ui = self.data.get("ui", {})
        editor = self.data.get("editor", {})
        lines = ["gitHelper profile summary:"]
        lines.append(f"- Default organisation: {github.get('default_org') or 'not set'}")
        preferred = github.get("preferred_repos") or []
        if preferred:
            lines.append("- Preferred repositories: " + ", ".join(preferred))
        else:
            lines.append("- Preferred repositories: none configured")
        lines.append(f"- Preferred editor: {editor.get('command')}")
        lines.append(f"- UI theme: {ui.get('theme', 'system')}")
        lines.append(f"- GUI fallback enabled: {'yes' if ui.get('use_gui') else 'no'}")
        return "\n".join(lines)


def _format_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        formatted = ", ".join(_format_value(item) for item in value)
        return f"[{formatted}]"
    return f'"{value}"'


def _dump_toml(data: Dict[str, Any]) -> str:
    lines: list[str] = []
    for section, values in data.items():
        lines.append(f"[{section}]")
        for key, value in values.items():
            lines.append(f"{key} = {_format_value(value)}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
