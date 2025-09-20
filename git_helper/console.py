"""Utilities for rendering colourful output in the terminal."""

from __future__ import annotations

import os
import shutil
import sys
from getpass import getpass
from typing import Iterable, Sequence

__all__ = [
    "banner",
    "bullet_list",
    "confirm",
    "error",
    "info",
    "prompt",
    "prompt_secret",
    "rule",
    "success",
    "warning",
]

RESET = "\033[0m"
STYLES = {
    "info": "\033[36m",
    "success": "\033[32m",
    "warning": "\033[33m",
    "error": "\033[31m",
    "title": "\033[95m",
    "bold": "\033[1m",
}


def _supports_color(stream: object) -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if not hasattr(stream, "isatty"):
        return False
    return bool(stream.isatty())


def _style(text: str, style: str, *, stream: object | None = None) -> str:
    stream = stream or sys.stdout
    if not _supports_color(stream):
        return text
    return f"{STYLES.get(style, '')}{text}{RESET}"


def banner(text: str) -> None:
    """Render a bold banner at the top of the screen."""

    width = shutil.get_terminal_size((80, 20)).columns
    title = text.strip()
    print(_style(title.center(width), "title"))
    rule()


def rule(character: str = "─") -> None:
    """Draw a horizontal rule using *character*."""

    width = shutil.get_terminal_size((80, 20)).columns
    print(_style(character * width, "bold"))


def info(message: str) -> None:
    print(_style(f"ℹ️  {message}", "info"))


def success(message: str) -> None:
    print(_style(f"✅ {message}", "success"))


def warning(message: str) -> None:
    print(_style(f"⚠️  {message}", "warning"))


def error(message: str) -> None:
    print(_style(f"❌ {message}", "error"), file=sys.stderr)


def prompt(message: str, *, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    prompt_text = _style(f"{message}{suffix}: ", "bold")
    response = input(prompt_text)
    if response.strip():
        return response.strip()
    return default or ""


def prompt_secret(message: str) -> str:
    prompt_text = _style(f"{message}: ", "bold")
    return getpass(prompt_text)


def confirm(message: str, *, default: bool = False) -> bool:
    options = "Y/n" if default else "y/N"
    prompt_text = _style(f"{message} [{options}]: ", "bold")
    while True:
        response = input(prompt_text).strip().lower()
        if not response:
            return default
        if response in {"y", "yes"}:
            return True
        if response in {"n", "no"}:
            return False
        warning("Please respond with 'y' or 'n'.")


def bullet_list(items: Sequence[str] | Iterable[str]) -> None:
    for item in items:
        print(_style(f"  • {item}", "info"))
