"""Configuration and theme helpers for the neon Git cockpit."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

import curses

CONFIG_DIR = Path.home() / ".config" / "neon_git"
CONFIG_FILE = CONFIG_DIR / "config.json"

# Mapping of theme names to basic colour roles. We keep the palette small so it
# works well in curses where only 8 base colours are guaranteed.
THEME_DEFINITIONS = {
    "github_dark": {
        "background": "black",
        "foreground": "white",
        "accent": "cyan",
        "panel": "blue",
        "muted": "magenta",
        "warning": "yellow",
        "success": "green",
        "danger": "red",
    },
    "matrix_green": {
        "background": "black",
        "foreground": "green",
        "accent": "green",
        "panel": "black",
        "muted": "cyan",
        "warning": "yellow",
        "success": "green",
        "danger": "red",
    },
    "neon_cyberpunk": {
        "background": "black",
        "foreground": "white",
        "accent": "magenta",
        "panel": "cyan",
        "muted": "blue",
        "warning": "yellow",
        "success": "green",
        "danger": "magenta",
    },
}

COLOR_NAME_TO_CURSES = {
    "black": curses.COLOR_BLACK,
    "blue": curses.COLOR_BLUE,
    "cyan": curses.COLOR_CYAN,
    "green": curses.COLOR_GREEN,
    "magenta": curses.COLOR_MAGENTA,
    "red": curses.COLOR_RED,
    "white": curses.COLOR_WHITE,
    "yellow": curses.COLOR_YELLOW,
}


@dataclass
class Theme:
    """Resolved theme definition."""

    name: str
    palette: Dict[str, int]


def _ensure_config_dir() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def _default_config() -> Dict[str, str]:
    return {"theme": "github_dark"}


def load_user_config() -> Dict[str, str]:
    """Load (and create) the user configuration file."""

    if not CONFIG_FILE.exists():
        _ensure_config_dir()
        CONFIG_FILE.write_text(json.dumps(_default_config(), indent=2))
    try:
        data = json.loads(CONFIG_FILE.read_text())
    except json.JSONDecodeError:
        data = _default_config()
    return data


def resolve_theme(preferred: str | None = None) -> Theme:
    """Return the active theme as a :class:`Theme`."""

    config = load_user_config()
    theme_name = preferred or config.get("theme", "github_dark")
    if theme_name not in THEME_DEFINITIONS:
        theme_name = "github_dark"
    palette = {
        role: COLOR_NAME_TO_CURSES.get(colour, curses.COLOR_WHITE)
        for role, colour in THEME_DEFINITIONS[theme_name].items()
    }
    return Theme(name=theme_name, palette=palette)


def apply_theme(theme: Theme) -> Dict[str, int]:
    """Initialise curses colour pairs for the theme."""

    curses.start_color()
    try:
        curses.use_default_colors()
    except curses.error:
        # Not all terminals support default colours; ignore.
        pass

    pairs = {
        "default": 1,
        "accent": 2,
        "panel": 3,
        "muted": 4,
        "warning": 5,
        "success": 6,
        "danger": 7,
    }

    curses.init_pair(pairs["default"], theme.palette["foreground"], theme.palette["background"])
    curses.init_pair(pairs["accent"], theme.palette["accent"], theme.palette["background"])
    curses.init_pair(pairs["panel"], theme.palette["foreground"], theme.palette["panel"])
    curses.init_pair(pairs["muted"], theme.palette["muted"], theme.palette["background"])
    curses.init_pair(pairs["warning"], theme.palette["warning"], theme.palette["background"])
    curses.init_pair(pairs["success"], theme.palette["success"], theme.palette["background"])
    curses.init_pair(pairs["danger"], theme.palette["danger"], theme.palette["background"])

    return pairs
