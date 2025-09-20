"""Configuration utilities for the gitHelper package."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

__all__ = [
    "CONFIG_DIR",
    "CONFIG_FILE",
    "DEFAULT_CONFIG",
    "load_config",
    "save_config",
]

CONFIG_DIR = Path.home() / ".config" / "git_helper"
CONFIG_FILE = CONFIG_DIR / "config.json"
DEFAULT_CONFIG: Dict[str, Any] = {
    "repository_root": str((Path.home() / "git").expanduser().resolve()),
}


def _ensure_config_dir() -> None:
    """Ensure that the configuration directory exists."""

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> Dict[str, Any]:
    """Load the persisted configuration.

    If the configuration file does not exist or is invalid JSON a default
    configuration is written to disk and returned.
    """

    if not CONFIG_FILE.exists():
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

    try:
        data = json.loads(CONFIG_FILE.read_text())
    except json.JSONDecodeError:
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

    merged = DEFAULT_CONFIG.copy()
    if isinstance(data, dict):
        merged.update({k: v for k, v in data.items() if isinstance(k, str)})
    if merged != data:
        save_config(merged)
    return merged


def save_config(data: Dict[str, Any]) -> None:
    """Persist *data* to the configuration file."""

    _ensure_config_dir()
    CONFIG_FILE.write_text(json.dumps(data, indent=2, sort_keys=True))
