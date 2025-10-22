"""Command palette implementation using prompt_toolkit."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Optional

from prompt_toolkit import prompt
from prompt_toolkit.completion import FuzzyWordCompleter
from prompt_toolkit.styles import Style

__all__ = ["CommandPalette", "PaletteCommand"]


@dataclass(frozen=True)
class PaletteCommand:
    """Definition of an interactive command palette entry."""

    name: str
    description: str


class CommandPalette:
    """Simple fuzzy-search command palette for the CLI."""

    def __init__(self, commands: Mapping[str, PaletteCommand]) -> None:
        self._commands = dict(commands)
        self._completer = FuzzyWordCompleter(list(self._commands.keys()), WORD=True)
        self._style = Style.from_dict({
            "prompt": "bold cyan",
            "completion-menu.completion": "bg:#202630 #f0f6fc",
            "completion-menu.completion.current": "bg:#0d7ef7 #ffffff",
        })

    def choose(self, message: str = "Command") -> Optional[PaletteCommand]:
        """Return the selected command or ``None`` if cancelled."""

        try:
            choice = prompt(
                [("class:prompt", f"{message}: ")],
                completer=self._completer,
                complete_while_typing=True,
                style=self._style,
            ).strip()
        except (EOFError, KeyboardInterrupt):  # pragma: no cover - interactive guard
            return None
        if not choice:
            return None
        command = self._commands.get(choice)
        return command

    def format_help(self) -> str:
        """Return formatted help text for palette commands."""

        lines = ["Available palette commands:"]
        for command in self._commands.values():
            lines.append(f"- {command.name}: {command.description}")
        return "\n".join(lines)
