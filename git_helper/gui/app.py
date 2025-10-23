"""KivyMD based GUI frontend for gitHelper."""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import Any, Optional

from ..diagnostics import DiagnosticEngine
from ..git_core import GitCore, GitCommandError
from ..gh_pages import GitHubPagesManager
from ..plugin_manager import PluginManager
from ..repo_manager import RepoManager
from ..ssh_tools import SSHTools
from ..utils.settings import SettingsManager

try:  # pragma: no cover - optional GUI dependency
    from kivy.clock import Clock
    from kivy.lang import Builder
    from kivy.properties import BooleanProperty, StringProperty
    from kivymd.app import MDApp
    from kivymd.uix.boxlayout import MDBoxLayout
    from kivymd.uix.list import (
        MDList,
        OneLineAvatarIconListItem,
        OneLineListItem,
        IconLeftWidget,
        RightSwitch,
    )
    from kivymd.uix.button import MDRaisedButton
    from kivymd.uix.snackbar import Snackbar
    from kivymd.uix.label import MDLabel
    from kivymd.uix.appbar import MDTopAppBar
    from kivymd.uix.screen import MDScreen
    from kivy.uix.screenmanager import ScreenManager
except ModuleNotFoundError:  # pragma: no cover - executed when GUI deps missing
    MDApp = None  # type: ignore[assignment]

KV_DEFINITION = """
#:import IconLeftWidget kivymd.uix.list.IconLeftWidget
#:import RightSwitch kivymd.uix.list.RightSwitch

<PluginToggle@OneLineAvatarIconListItem>:
    plugin_name: ""
    active: True
    text: root.plugin_name
    IconLeftWidget:
        icon: "puzzle"
    RightSwitch:
        id: toggle
        active: root.active
        on_active: app.on_plugin_toggle(root.plugin_name, self.active)

MDNavigationLayout:
    ScreenManager:
        id: screen_manager
        MDScreen:
            name: "repositories"
            MDBoxLayout:
                orientation: "vertical"
                MDTopAppBar:
                    title: "Repositories"
                    left_action_items: [["menu", lambda x: nav_drawer.set_state("toggle")]]
                ScrollView:
                    MDList:
                        id: repo_list
                MDBoxLayout:
                    adaptive_height: True
                    padding: "12dp"
                    MDLabel:
                        id: status_label
                        text: "Status:"
        MDScreen:
            name: "git"
            MDBoxLayout:
                orientation: "vertical"
                MDTopAppBar:
                    title: "Git Dashboard"
                    left_action_items: [["menu", lambda x: nav_drawer.set_state("toggle")]]
                ScrollView:
                    MDList:
                        id: git_log
        MDScreen:
            name: "ssh"
            MDBoxLayout:
                orientation: "vertical"
                MDTopAppBar:
                    title: "SSH Manager"
                    left_action_items: [["menu", lambda x: nav_drawer.set_state("toggle")]]
                ScrollView:
                    MDList:
                        id: ssh_keys
        MDScreen:
            name: "plugins"
            MDBoxLayout:
                orientation: "vertical"
                MDTopAppBar:
                    title: "Plugin Centre"
                    left_action_items: [["menu", lambda x: nav_drawer.set_state("toggle")]]
                ScrollView:
                    MDList:
                        id: plugin_list
        MDScreen:
            name: "diagnostics"
            MDBoxLayout:
                orientation: "vertical"
                MDTopAppBar:
                    title: "Diagnostics"
                    left_action_items: [["menu", lambda x: nav_drawer.set_state("toggle")]]
                MDBoxLayout:
                    orientation: "vertical"
                    padding: "12dp"
                    spacing: "12dp"
                    MDLabel:
                        id: diagnostics_summary
                        text: "Run CodeBreakAnalyzer to detect regressions."
                        theme_text_color: "Secondary"
                    MDRaisedButton:
                        text: "Run CodeBreakAnalyzer"
                        on_release: app.run_code_break_analyzer()
        MDScreen:
            name: "settings"
            MDBoxLayout:
                orientation: "vertical"
                MDTopAppBar:
                    title: "Settings"
                    left_action_items: [["menu", lambda x: nav_drawer.set_state("toggle")]]
                MDBoxLayout:
                    orientation: "vertical"
                    padding: "12dp"
                    spacing: "12dp"
                    MDLabel:
                        id: theme_label
                        text: "Theme:"
                    MDRaisedButton:
                        text: "Switch Theme"
                        on_release: app.toggle_theme()
    MDNavigationDrawer:
        id: nav_drawer
        BoxLayout:
            orientation: "vertical"
            spacing: "8dp"
            padding: "12dp"
            MDLabel:
                text: "gitHelper"
                font_style: "H4"
                size_hint_y: None
                height: self.texture_size[1]
            ScrollView:
                MDList:
                    OneLineListItem:
                        text: "Repositories"
                        on_release: app.switch_screen("repositories")
                    OneLineListItem:
                        text: "Git"
                        on_release: app.switch_screen("git")
                    OneLineListItem:
                        text: "SSH"
                        on_release: app.switch_screen("ssh")
                    OneLineListItem:
                        text: "Plugins"
                        on_release: app.switch_screen("plugins")
                    OneLineListItem:
                        text: "Diagnostics"
                        on_release: app.switch_screen("diagnostics")
                    OneLineListItem:
                        text: "Settings"
                        on_release: app.switch_screen("settings")
"""


class MissingGuiDependencies(RuntimeError):
    """Raised when optional GUI dependencies are not installed."""


if MDApp:  # pragma: no cover - executed only when GUI dependencies installed

    class PluginToggle(OneLineAvatarIconListItem):
        plugin_name = StringProperty()
        active = BooleanProperty(True)


    class GitHelperApp(MDApp):
        """Main KivyMD application."""

        def __init__(self, *, path: str | Path | None = None, theme: str | None = None) -> None:
            super().__init__()
            self.settings = SettingsManager()
            self.repo_path = Path(path or Path.cwd())
            self.git = GitCore(self.repo_path)
            self.repo_manager = RepoManager()
            self.ssh = SSHTools()
            self.plugins = PluginManager(self.git)
            self.diagnostics = DiagnosticEngine(self.git)
            self.github_pages = GitHubPagesManager(self.git)
            self.command_log: list[str] = []
            self.requested_theme = theme or self.settings.get("theme", "system")

        def build(self):  # type: ignore[override]
            self.title = "gitHelper GUI"
            root = Builder.load_string(KV_DEFINITION)
            Clock.schedule_once(lambda *_: self._post_build())
            return root

        # ------------------------------------------------------------------ startup
        def _post_build(self) -> None:
            self.apply_theme(self.requested_theme)
            self.refresh_repositories()
            self.refresh_git_log()
            self.refresh_ssh_keys()
            self.refresh_plugins()
            self.refresh_status()

        # ----------------------------------------------------------------- theming
        def apply_theme(self, theme: str | None) -> None:
            if not theme or theme == "system":
                self.theme_cls.theme_style = "Light"
            elif theme == "neon_dark":
                self.theme_cls.theme_style = "Dark"
                self.theme_cls.primary_palette = "Purple"
            else:
                self.theme_cls.theme_style = "Light"
            self.settings.set("theme", theme or "system")
            theme_label = self.root.ids.get("theme_label")
            if theme_label:
                theme_label.text = f"Theme: {theme or 'system'}"

        def toggle_theme(self) -> None:
            current = self.settings.get("theme", "system")
            new_theme = "neon_dark" if current != "neon_dark" else "system"
            self.apply_theme(new_theme)

        # ---------------------------------------------------------------- navigation
        def switch_screen(self, name: str) -> None:
            self.root.ids.screen_manager.current = name
            self.root.ids.nav_drawer.set_state("close")

        # ---------------------------------------------------------------- commands
        def prompt(self, message: str) -> str:
            # GUI prompt deferred for future iterations. Return empty query for now.
            self.log_message(f"Prompt requested: {message}")
            return ""

        def show_popup(self, title: str, body: str) -> None:
            Snackbar(text=f"{title}: {body}", duration=3).open()

        def log_message(self, message: str) -> None:
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            entry = f"[{timestamp}] {message}"
            self.command_log.append(entry)
            git_log = self.root.ids.get("git_log")
            if isinstance(git_log, MDList):
                git_log.clear_widgets()
                for item in self.command_log[-50:]:
                    git_log.add_widget(OneLineListItem(text=item))

        # ---------------------------------------------------------------- refreshers
        def refresh_status(self) -> None:
            status_label = self.root.ids.get("status_label")
            if not status_label:
                return
            try:
                branch = self.git.current_branch() or "detached"
                tracking = self.git.tracking_branch() or "no upstream"
                status = self.git.status()
                status_label.text = f"Branch: {branch} | Tracking: {tracking}\n{status}"
            except GitCommandError as exc:
                status_label.text = f"Status unavailable: {exc}"

        def refresh_repositories(self) -> None:
            repo_list = self.root.ids.get("repo_list")
            if not isinstance(repo_list, MDList):
                return
            repo_list.clear_widgets()
            try:
                repositories = self.repo_manager.list()
            except Exception as exc:  # pragma: no cover - depends on configuration
                repositories = []
                self.log_message(f"Failed to list repositories: {exc}")
            if not repositories:
                repo_list.add_widget(OneLineListItem(text="No repositories configured."))
            for repo in repositories:
                item = OneLineListItem(text=str(repo))
                repo_list.add_widget(item)

        def refresh_git_log(self) -> None:
            try:
                history = self.git.log(limit=20)
            except GitCommandError as exc:
                history = str(exc)
            self.log_message(history)

        def refresh_ssh_keys(self) -> None:
            ssh_list = self.root.ids.get("ssh_keys")
            if not isinstance(ssh_list, MDList):
                return
            ssh_list.clear_widgets()
            for key in self.ssh.list_keys():
                ssh_list.add_widget(OneLineListItem(text=str(key)))
            if not ssh_list.children:
                ssh_list.add_widget(OneLineListItem(text="No SSH keys found."))

        def refresh_plugins(self) -> None:
            plugin_list = self.root.ids.get("plugin_list")
            if not isinstance(plugin_list, MDList):
                return
            plugin_list.clear_widgets()
            for state in self.plugins.discover(force=True):
                toggle = PluginToggle(plugin_name=state.plugin.name, active=state.enabled)
                plugin_list.add_widget(toggle)

        # --------------------------------------------------------------- plugin API
        def on_plugin_toggle(self, name: str, active: bool) -> None:
            if active:
                self.plugins.enable(name)
                self.log_message(f"Plugin enabled: {name}")
            else:
                self.plugins.disable(name)
                self.log_message(f"Plugin disabled: {name}")

        def run_plugin(self, name: str) -> None:
            try:
                message = self.plugins.run_plugin(name, self)
            except Exception as exc:  # pragma: no cover - plugin behaviour varies
                self.show_popup("Plugin Error", str(exc))
                return
            self.show_popup(name, message)
            self.log_message(f"Plugin executed: {name}")

        def run_code_break_analyzer(self) -> None:
            try:
                summary = self.plugins.run_plugin("CodeBreakAnalyzer", self)
            except ValueError:
                summary = self._run_bisect_direct()
            self.root.ids.diagnostics_summary.text = summary
            self.log_message(summary)

        def _run_bisect_direct(self) -> str:
            try:
                result = self.diagnostics.find_breaking_commit()
                return result
            except GitCommandError as exc:
                return f"Diagnostics unavailable: {exc}"

else:  # pragma: no cover - executed when GUI dependencies missing

    class GitHelperApp:  # type: ignore[override]
        def __init__(self, *_, **__):
            raise MissingGuiDependencies(
                "KivyMD is not installed. Install 'kivy' and 'kivymd' to use the GUI."
            )


def launch_gui(*, path: str | Path | None = None, theme: Optional[str] = None) -> None:
    """Launch the interactive GUI if available."""

    if MDApp is None:
        raise MissingGuiDependencies(
            "KivyMD is not installed. Install 'kivy' and 'kivymd' to use the GUI."
        )
    app = GitHelperApp(path=path, theme=theme)
    app.run()


__all__ = ["launch_gui", "GitHelperApp", "MissingGuiDependencies"]
