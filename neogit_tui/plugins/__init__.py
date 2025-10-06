"""Plugin loading for the neon Git cockpit."""

from __future__ import annotations

from dataclasses import dataclass  # [REF] preparing for richer plugin validation
from importlib import import_module  # [REF] enable dynamic module discovery
from pathlib import Path  # [REF] allow directory-based plugin loading
from typing import Any, Callable, List  # [REF] preserve explicit type contracts

from ..git import GitInterface


@dataclass
class Plugin:  # [REF] retain plugin contract for registration checks
    name: str  # [REF] document expected plugin metadata
    description: str  # [REF] document expected plugin metadata
    run: Callable[[GitInterface, Any], str]  # [REF] enforce callable signature for execution


def load_plugins(git: GitInterface) -> List[Plugin]:  # [REF] require active GitInterface for registration
    plugins: List[Plugin] = []  # [REF] accumulate successfully registered plugins
    base = Path(__file__).parent  # [REF] resolve plugin directory root
    for entry in sorted(base.iterdir()):  # [REF] iterate over both files and packages deterministically
        if entry.name.startswith("__"):  # [REF] skip sentinel files and caches
            continue  # [REF] ignore non-plugin infrastructure artefacts
        module_name: str  # [REF] declare ahead for clarity with mypy
        if entry.is_dir() and (entry / "__init__.py").exists():  # [REF] allow package-based plug-ins
            module_name = f"{__name__}.{entry.name}"  # [REF] construct import path for package plugin
        elif entry.is_file() and entry.suffix == ".py":  # [REF] include legacy single-file plug-ins
            module_name = f"{__name__}.{entry.stem}"  # [REF] construct import path for module plugin
        else:  # [REF] reject unrelated filesystem entries
            continue  # [REF] move to next candidate entry
        try:
            module = import_module(module_name)  # [REF] dynamically import plugin module
        except Exception:
            continue  # [REF] suppress faulty plugin imports to keep TUI responsive
        register = getattr(module, "register", None)  # [REF] discover mandatory register hook
        if not callable(register):  # [REF] ensure register exposes callable contract
            continue  # [REF] skip modules lacking valid registration hook
        try:
            plugin = register(git)  # [REF] provide active GitInterface to registration routine
        except Exception:
            continue  # [REF] shield host app from plugin registration errors
        if isinstance(plugin, Plugin):  # [REF] accept only well-formed plugin payloads
            plugins.append(plugin)  # [REF] retain validated plugin for runtime use
    plugins.sort(key=lambda plug: plug.name.lower())  # [REF] keep deterministic plugin ordering for UI
    return plugins  # [REF] surface collected plug-ins to the caller
