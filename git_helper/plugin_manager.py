"""Dynamic plug-in loader bridging CLI, TUI, and GUI frontends."""

from __future__ import annotations

from dataclasses import dataclass
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Iterable, List, Optional

from neogit_tui.plugins import Plugin

from .utils.settings import SettingsManager

__all__ = ["PluginManager", "PluginState"]


@dataclass
class PluginState:
    plugin: Plugin
    enabled: bool = True


class PluginManager:
    """Discover and manage plug-ins across frontends."""

    def __init__(self, git_interface, search_paths: Optional[Iterable[Path]] = None,
                 settings: Optional[SettingsManager] = None) -> None:
        self.git = git_interface
        self.settings = settings or SettingsManager()
        base_dir = Path(__file__).resolve().parent
        self.search_paths: List[tuple[Path, str]] = [(base_dir / "plugins", "git_helper.plugins")]
        tui_plugins = base_dir.parent / "neogit_tui" / "plugins"
        if tui_plugins.exists():
            self.search_paths.append((tui_plugins, "neogit_tui.plugins"))
        if search_paths:
            for index, path in enumerate(search_paths):
                root = Path(path)
                prefix = f"git_helper.dynamic_plugins.{index}"
                self.search_paths.append((root, prefix))
        self._loaded: List[PluginState] | None = None

    # ---------------------------------------------------------------- discovery
    def discover(self, *, force: bool = False) -> List[PluginState]:
        if self._loaded is not None and not force:
            return self._loaded
        discovered: List[PluginState] = []
        disabled = set(self.settings.disabled_plugins())
        for path, prefix in self.search_paths:
            if not path.exists():
                continue
            for entry in sorted(path.iterdir()):
                if entry.name.startswith("__"):
                    continue
                module = self._import_plugin(entry, prefix)
                if not module:
                    continue
                register = getattr(module, "register", None)
                if not callable(register):
                    continue
                try:
                    plugin = register()
                except TypeError:
                    plugin = register(self.git)
                except Exception:
                    continue
                if not isinstance(plugin, Plugin):
                    continue
                discovered.append(PluginState(plugin=plugin, enabled=plugin.name not in disabled))
        discovered.sort(key=lambda state: state.plugin.name.lower())
        self._loaded = discovered
        return discovered

    def _import_plugin(self, entry: Path, prefix: str) -> ModuleType | None:
        if entry.is_dir() and (entry / "__init__.py").exists():
            location = entry / "__init__.py"
            module_name = f"{prefix}.{entry.name}"
        elif entry.is_file() and entry.suffix == ".py":
            location = entry
            module_name = f"{prefix}.{entry.stem}"
        else:
            return None
        try:
            spec = importlib.util.spec_from_file_location(module_name, location)
            if not spec or not spec.loader:
                return None
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            return module
        except Exception:
            return None

    # ----------------------------------------------------------------- settings
    def enable(self, plugin_name: str) -> None:
        self.settings.enable_plugin(plugin_name)
        self._loaded = None

    def disable(self, plugin_name: str) -> None:
        self.settings.disable_plugin(plugin_name)
        self._loaded = None

    def get_enabled_plugins(self) -> List[Plugin]:
        return [state.plugin for state in self.discover() if state.enabled]

    def run_plugin(self, name: str, app_context) -> str:
        for state in self.discover():
            if state.plugin.name == name and state.enabled:
                return state.plugin.run(self.git, app_context)
        raise ValueError(f"Plugin '{name}' is not enabled or does not exist.")

