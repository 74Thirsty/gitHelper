"""Plugin loading for the neon Git cockpit."""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import Any, Callable, List

from ..git import GitInterface


@dataclass
class Plugin:
    name: str
    description: str
    run: Callable[[GitInterface, Any], str]


def load_plugins() -> List[Plugin]:
    plugins: List[Plugin] = []
    base = Path(__file__).parent
    for module_path in base.glob("*.py"):
        if module_path.name == "__init__.py":
            continue
        module_name = f"{__name__}.{module_path.stem}"
        try:
            module = import_module(module_name)
        except Exception:
            continue
        register = getattr(module, "register", None)
        if register is None:
            continue
        try:
            plugin = register()
        except Exception:
            continue
        if plugin:
            plugins.append(plugin)
    plugins.sort(key=lambda plug: plug.name.lower())
    return plugins
