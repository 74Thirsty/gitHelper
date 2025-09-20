"""Curses powered neon Git cockpit."""

from __future__ import annotations

import curses
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .config import apply_theme, resolve_theme
from .git import Commit, GitCommandError, GitInterface, HeadSnapshot
from .github import GitHubClient, GitHubItem, GitHubUnavailable, WorkflowRun, try_create_client
from .plugins import Plugin, load_plugins


@dataclass
class RebaseEntry:
    commit: Commit
    action: str = "pick"


@dataclass
class AppState:
    commits: List[Commit]
    selected: int = 0
    view: str = "diff"  # diff, branches, github, danger, rebase, plugins
    status: str = "Welcome to the neon cockpit."
    help_visible: bool = False
    undo_stack: List[HeadSnapshot] = field(default_factory=list)
    redo_stack: List[HeadSnapshot] = field(default_factory=list)
    github_tab: str = "issues"
    github_error: Optional[str] = None
    plugin_output: Optional[str] = None
    rebase_entries: List[RebaseEntry] = field(default_factory=list)
    rebase_cursor: int = 0
    plugin_index: int = 0
    danger_mode: bool = False


HELP_TEXT = [
    "Arrows: navigate commits",
    "Enter: focus diff",
    "Space: checkout commit in temp branch",
    "Tab: create branch from commit",
    "F: fast-forward to main",
    "M: merge preview",
    "B: branch playground",
    "G: GitHub sync center",
    "R: interactive rebase planner",
    "P: run plug-ins",
    "D: danger zone",
    "U: undo | Shift+U: redo",
    "/: search (#42 hits GitHub)",
    "?: toggle this help",
    "Q: exit",
]

GITHUB_TABS = ["issues", "pulls", "actions"]

HEADER_HEIGHT = 3
STATUS_HEIGHT = 2
MIN_BODY_HEIGHT = 8
MIN_TIMELINE_WIDTH = 30
MIN_DETAIL_WIDTH = 28
MIN_TOTAL_HEIGHT = HEADER_HEIGHT + STATUS_HEIGHT + MIN_BODY_HEIGHT
MIN_TOTAL_WIDTH = MIN_TIMELINE_WIDTH + MIN_DETAIL_WIDTH

class NeonGitApp:
    def __init__(self, stdscr: curses.window):
        self.stdscr = stdscr
        self.git = GitInterface()
        self.theme = resolve_theme()
        self.colors = apply_theme(self.theme)
        curses.curs_set(0)
        self.stdscr.keypad(True)
        self.stdscr.timeout(200)
        commits = self.git.list_commits()
        self.state = AppState(commits=commits)
        self.diff_cache: Dict[str, str] = {}
        self.github: Optional[GitHubClient] = try_create_client(self.git)
        if not self.github:
            self.state.github_error = "GitHub CLI unavailable or remote not set."
        self.github_cache: Dict[str, List[GitHubItem] | List[WorkflowRun]] = {}
        self.plugins: List[Plugin] = load_plugins()
        self.state.status = f"Loaded {len(commits)} commits. Press ? for help."
        self._header_win: Optional[curses.window] = None
        self._timeline_win: Optional[curses.window] = None
        self._detail_win: Optional[curses.window] = None
        self._status_win: Optional[curses.window] = None

    # ------------------------------------------------------------------ rendering
    def render(self) -> None:
        max_y, max_x = self.stdscr.getmaxyx()
        layout = self._layout_windows(max_y, max_x)
        if not layout:
            self._render_resize_hint(max_y, max_x)
            return

        header_win, timeline_win, detail_win, status_win = layout

        # ⚡ FIX: don’t erase stdscr, just render child windows
        self._render_header(header_win)
        self._render_timeline(timeline_win)
        self._render_detail(detail_win)
        self._render_status(status_win)

        if self.state.help_visible:
            self._render_help_overlay()
        if self.state.danger_mode:
            self._render_danger_overlay()

        # ⚡ FIX: actually push all windows to the terminal
        curses.doupdate()


    def _layout_windows(
        self, max_y: int, max_x: int
    ) -> Optional[Tuple[curses.window, curses.window, curses.window, curses.window]]:
        if max_y < MIN_TOTAL_HEIGHT or max_x < MIN_TOTAL_WIDTH:
            self._clear_window_cache()
            return None

        body_height = max_y - HEADER_HEIGHT - STATUS_HEIGHT
        if body_height < MIN_BODY_HEIGHT:
            self._clear_window_cache()
            return None

        timeline_width = max(int(max_x * 0.45), MIN_TIMELINE_WIDTH)
        max_timeline_width = max_x - MIN_DETAIL_WIDTH
        if max_timeline_width < MIN_TIMELINE_WIDTH:
            self._clear_window_cache()
            return None
        timeline_width = min(timeline_width, max_timeline_width)
        detail_width = max_x - timeline_width
        if detail_width < MIN_DETAIL_WIDTH:
            detail_width = MIN_DETAIL_WIDTH
            timeline_width = max_x - detail_width
        if timeline_width < MIN_TIMELINE_WIDTH or detail_width < MIN_DETAIL_WIDTH:
            self._clear_window_cache()
            return None

        try:
            header_win = self._create_or_resize_window("_header_win", HEADER_HEIGHT, max_x, 0, 0)
            timeline_win = self._create_or_resize_window(
                "_timeline_win", body_height, timeline_width, HEADER_HEIGHT, 0
            )
            detail_win = self._create_or_resize_window(
                "_detail_win", body_height, detail_width, HEADER_HEIGHT, timeline_width
            )
            status_win = self._create_or_resize_window(
                "_status_win", STATUS_HEIGHT, max_x, HEADER_HEIGHT + body_height, 0
            )
        except curses.error:
            self._clear_window_cache()
            return None

        return header_win, timeline_win, detail_win, status_win

    def _create_or_resize_window(
        self, attr: str, height: int, width: int, y: int, x: int
    ) -> curses.window:
        win = getattr(self, attr)
        if win is None:
            win = curses.newwin(height, width, y, x)
            setattr(self, attr, win)
        else:
            win.resize(height, width)
            win.mvwin(y, x)
        return win

    def _clear_window_cache(self) -> None:
        for attr in ("_header_win", "_timeline_win", "_detail_win", "_status_win"):
            win = getattr(self, attr)
            if win is not None:
                setattr(self, attr, None)

    def _render_resize_hint(self, max_y: int, max_x: int) -> None:
        self.stdscr.erase()
        lines = [
            "Neon cockpit needs more space!",
            f"Increase terminal to at least {MIN_TOTAL_WIDTH}x{MIN_TOTAL_HEIGHT} characters.",
            "Resize the window and the UI will auto-refresh.",
        ]
        start_y = max((max_y - len(lines)) // 2, 0)
        for idx, line in enumerate(lines):
            y = start_y + idx
            if y >= max_y:
                break
            x = max((max_x - len(line)) // 2, 0)
            try:
                attr = curses.A_BOLD if idx == 0 else 0
                available_width = max_x - x
                if available_width <= 0:
                    continue
                self.stdscr.addstr(y, x, line[:available_width], attr)
            except curses.error:
                continue
        self.stdscr.refresh()

    def _render_header(self, win: curses.window) -> None:
        win.bkgd(" ", curses.color_pair(self.colors["panel"]))
        win.erase()
        title = " NEON GIT COCKPIT "
        win.addstr(1, 2, title, curses.color_pair(self.colors["accent"]) | curses.A_BOLD)
        branch = self.git.current_branch() or "detached"
        win.addstr(1, len(title) + 3, f"| HEAD: {branch}")
        win.addstr(1, len(title) + 22, f"| Theme: {self.theme.name}")
        win.addstr(1, len(title) + 45, f"| View: {self.state.view}")
        win.refresh()

    def _render_timeline(self, win: curses.window) -> None:
        win.erase()
        win.box()
        height, width = win.getmaxyx()
        available = height - 2
        start = max(0, self.state.selected - available + 1)
        end = min(len(self.state.commits), start + available)
        for idx, commit in enumerate(self.state.commits[start:end], start=start):
            marker = "➤" if idx == self.state.selected else " "
            subject = commit.subject[: width - 20]
            line = f"{marker} {commit.short_hash} {commit.date} {commit.author[:8]:<8} {subject}"
            attr = curses.color_pair(self.colors["default"])
            if idx == self.state.selected:
                attr |= curses.A_REVERSE
            win.addstr(idx - start + 1, 1, line.ljust(width - 2), attr)
        win.refresh()

    def _render_detail(self, win: curses.window) -> None:
        win.erase()
        win.box()
        height, width = win.getmaxyx()
        content_width = width - 4
        if not self.state.commits:
            win.addstr(1, 2, "No commits found")
            win.refresh()
            return

        if self.state.view == "diff":
            commit = self.state.commits[self.state.selected]
            text = self._get_diff(commit)
            self._draw_text_block(win, text, content_width)
        elif self.state.view == "branches":
            graph = self.git.branch_graph()
            self._draw_text_block(win, graph, content_width)
        elif self.state.view == "github":
            self._render_github_panel(win, content_width)
        elif self.state.view == "rebase":
            self._render_rebase_panel(win, content_width)
        elif self.state.view == "plugins":
            self._render_plugin_panel(win, content_width)
        elif self.state.view == "danger":
            self._render_danger_panel(win, content_width)
        else:
            win.addstr(1, 2, f"Unknown view: {self.state.view}")
        win.refresh()

    def _render_status(self, win: curses.window) -> None:
        win.bkgd(" ", curses.color_pair(self.colors["panel"]))
        win.erase()
        status = self.state.status[: win.getmaxyx()[1] - 2]
        win.addstr(0, 1, status)
        undo_redo = f"Undo:{len(self.state.undo_stack)} | Redo:{len(self.state.redo_stack)}"
        win.addstr(1, 1, undo_redo, curses.color_pair(self.colors["muted"]))
        win.refresh()

    def _draw_text_block(self, win: curses.window, text: str, width: int) -> None:
        lines = text.splitlines()
        height, _ = win.getmaxyx()
        max_lines = height - 2
        for idx, line in enumerate(lines[:max_lines]):
            attr = curses.color_pair(self.colors["default"])
            if line.startswith("+"):
                attr = curses.color_pair(self.colors["success"])
            elif line.startswith("-"):
                attr = curses.color_pair(self.colors["danger"])
            elif line.startswith("commit"):
                attr = curses.color_pair(self.colors["accent"]) | curses.A_BOLD
            win.addstr(idx + 1, 2, line[:width], attr)

    # ------------------------------------------------------------- detail panels
    def _render_github_panel(self, win: curses.window, width: int) -> None:
        if self.state.github_error:
            win.addstr(1, 2, self.state.github_error)
            return
        if not self.github:
            win.addstr(1, 2, "GitHub features unavailable.")
            return
        win.addstr(1, 2, f"GitHub {self.state.github_tab.title()} (←/→ to switch)", curses.A_BOLD)
        items = self._ensure_github_data(self.state.github_tab)
        lines = []
        if self.state.github_tab == "actions":
            for run in items:  # type: ignore[assignment]
                assert isinstance(run, WorkflowRun)
                lines.append(f"▶ {run.name} | {run.status} | {run.conclusion or '—'}")
                lines.append(f"   {run.created_at} -> {run.url}")
        else:
            for item in items:  # type: ignore[assignment]
                assert isinstance(item, GitHubItem)
                lines.append(f"#{item.number} [{item.state}] {item.title}")
                lines.append(f"   by {item.author} @ {item.updated_at}")
                lines.append(f"   {item.url}")
        if not lines:
            lines.append("No data retrieved yet.")
        self._draw_text_block(win, "\n".join(lines), width)

    def _render_rebase_panel(self, win: curses.window, width: int) -> None:
        if not self.state.rebase_entries:
            win.addstr(1, 2, "No commits queued for rebase.")
            return
        win.addstr(1, 2, "Interactive Rebase Plan (Enter to launch, Esc to cancel)", curses.A_BOLD)
        for idx, entry in enumerate(self.state.rebase_entries):
            prefix = "➤" if idx == self.state.rebase_cursor else " "
            line = f"{prefix} {entry.action:<7} {entry.commit.short_hash} {entry.commit.subject}"
            attr = curses.color_pair(self.colors["default"])
            if idx == self.state.rebase_cursor:
                attr |= curses.A_REVERSE
            win.addstr(idx + 2, 2, line[:width], attr)
        win.addstr(len(self.state.rebase_entries) + 3, 2, "Keys: p pick | s squash | f fixup | e edit | r reword | x drop")

    def _render_plugin_panel(self, win: curses.window, width: int) -> None:
        if not self.plugins:
            win.addstr(1, 2, "No plug-ins discovered. Drop modules into plugins/ to extend.")
            return
        win.addstr(1, 2, "Plug-ins (Enter to run) - output on the right", curses.A_BOLD)
        for idx, plugin in enumerate(self.plugins):
            prefix = "➤" if idx == self.state.plugin_index else " "
            line = f"{prefix} {plugin.name}: {plugin.description}"
            attr = curses.color_pair(self.colors["default"])
            if idx == self.state.plugin_index:
                attr |= curses.A_REVERSE
            win.addstr(idx + 2, 2, line[:width], attr)
        if self.state.plugin_output:
            lines = self.state.plugin_output.splitlines()
            height, _ = win.getmaxyx()
            split = min(len(lines), height - 2)
            for idx in range(split):
                win.addstr(idx + 1, width // 2, lines[idx][: width // 2 - 2])

    def _render_danger_panel(self, win: curses.window, width: int) -> None:
        skull = [
            "      .-.",
            "     (o o)",
            "  .oooO--(_)--Oooo."
        ]
        for idx, line in enumerate(skull):
            win.addstr(idx + 1, 2, line, curses.color_pair(self.colors["danger"]))
        instructions = [
            "Danger Zone", "", "R: rollback to selected commit (hard reset)",
            "P: force push current branch", "S: stash working tree", "Esc: close",
        ]
        for idx, line in enumerate(instructions):
            win.addstr(idx + 1, 20, line[: width - 22])

    def _render_help_overlay(self) -> None:
        max_y, max_x = self.stdscr.getmaxyx()
        height = len(HELP_TEXT) + 4
        width = max(len(line) for line in HELP_TEXT) + 6
        win = curses.newwin(height, width, max_y // 2 - height // 2, max_x // 2 - width // 2)
        win.bkgd(" ", curses.color_pair(self.colors["panel"]))
        win.box()
        win.addstr(1, 2, "Hotkeys", curses.A_BOLD)
        for idx, line in enumerate(HELP_TEXT, start=2):
            win.addstr(idx, 2, line)
        win.refresh()

    def _render_danger_overlay(self) -> None:
        max_y, max_x = self.stdscr.getmaxyx()
        height = 10
        width = 60
        win = curses.newwin(height, width, max_y // 2 - height // 2, max_x // 2 - width // 2)
        win.bkgd(" ", curses.color_pair(self.colors["danger"]))
        win.box()
        win.addstr(1, 2, "!!! DANGER ZONE !!!", curses.A_BOLD)
        win.addstr(3, 2, "Press R to rollback, P to force push, S to stash. Esc closes.")
        win.addstr(5, 2, "Animated skull incoming... ☠")
        win.refresh()

    # -------------------------------------------------------------- data helpers
    def _get_diff(self, commit: Commit) -> str:
        if commit.hash not in self.diff_cache:
            try:
                diff = self.git.get_diff(commit.hash)
            except GitCommandError as exc:
                diff = f"Failed to load diff: {exc}"
            self.diff_cache[commit.hash] = diff
        return self.diff_cache[commit.hash]

    def _ensure_github_data(self, tab: str):
        if tab in self.github_cache:
            return self.github_cache[tab]
        if not self.github:
            return []
        try:
            if tab == "issues":
                data = self.github.list_issues()
            elif tab == "pulls":
                data = self.github.list_pull_requests()
            else:
                data = self.github.list_workflows()
            self.github_cache[tab] = data
            return data
        except GitHubUnavailable as exc:
            self.state.github_error = str(exc)
            return []

    # --------------------------------------------------------------- interactions
    def run(self) -> None:
        while True:
            self.render()
            key = self.stdscr.getch()
            if key == -1:
                continue
            if not self.handle_key(key):
                break

    def handle_key(self, key: int) -> bool:
        if key in (ord("q"), ord("Q")):
            return False
        if key == ord("?"):
            self.state.help_visible = not self.state.help_visible
            return True
        if key in (ord("d"), ord("D")):
            if self.state.danger_mode:
                self.state.danger_mode = False
                self.state.view = "diff"
            else:
                self.state.view = "danger"
                self.state.danger_mode = True
            return True
        if self.state.danger_mode:
            return self._handle_danger_key(key)
        if self.state.view == "rebase":
            return self._handle_rebase_key(key)
        if self.state.view == "plugins":
            return self._handle_plugin_key(key)
        if key in (curses.KEY_UP, ord("k")):
            self._move_selection(-1)
            return True
        if key in (curses.KEY_DOWN, ord("j")):
            self._move_selection(1)
            return True
        if key == curses.KEY_PPAGE:
            self._move_selection(-5)
            return True
        if key == curses.KEY_NPAGE:
            self._move_selection(5)
            return True
        if key == ord("g"):
            self.state.view = "github"
            self._ensure_github_data(self.state.github_tab)
            return True
        if key == ord("b") or key == ord("B"):
            self.state.view = "branches"
            return True
        if key == ord("r") or key == ord("R"):
            self._open_rebase_planner()
            return True
        if key == ord("p"):
            self._stash_worktree()
            return True
        if key == ord("P"):
            self.state.view = "plugins"
            return True
        if key == ord("u"):
            self._undo()
            return True
        if key == ord("U"):
            self._redo()
            return True
        if key == ord("/"):
            self._search()
            return True
        if key in (curses.KEY_LEFT, curses.KEY_RIGHT):
            if self.state.view == "github":
                self._cycle_github_tab(-1 if key == curses.KEY_LEFT else 1)
            return True
        if key == ord(" "):
            self._checkout_temp_branch()
            return True
        if key == ord("\t"):
            self._create_branch_from_commit()
            return True
        if key == ord("f") or key == ord("F"):
            self._fast_forward()
            return True
        if key == ord("m") or key == ord("M"):
            self._merge()
            return True
        if key == ord("\n"):
            self.state.view = "diff"
            return True
        return True

    def _move_selection(self, delta: int) -> None:
        new_index = min(max(self.state.selected + delta, 0), len(self.state.commits) - 1)
        if new_index != self.state.selected:
            self.state.selected = new_index
            self.state.status = f"Selected commit {self.state.commits[new_index].short_hash}"

    # ----------------------------------------------------------- git operations
    def _checkout_temp_branch(self) -> None:
        commit = self.state.commits[self.state.selected]
        if not self._confirm(f"Checkout {commit.short_hash} in temp branch?"):
            return
        snapshot = self.git.snapshot_head()
        try:
            branch = self.git.checkout_temporary_branch(commit)
        except GitCommandError as exc:
            self.state.status = str(exc)
            return
        self.state.undo_stack.append(snapshot)
        self.state.redo_stack.clear()
        self.state.status = f"Checked out {commit.short_hash} into {branch}"

    def _create_branch_from_commit(self) -> None:
        commit = self.state.commits[self.state.selected]
        default = f"feature/{commit.subject[:20].replace(' ', '-').lower()}"
        name = self._prompt("New branch name:", default=default)
        if not name:
            return
        try:
            self.git.create_branch(name, commit.hash)
            self.state.status = f"Branch {name} created at {commit.short_hash}"
        except GitCommandError as exc:
            self.state.status = str(exc)

    def _fast_forward(self) -> None:
        snapshot = self.git.snapshot_head()
        try:
            branch = self.git.fast_forward()
            self.state.status = f"Fast-forwarded to origin/{branch}"
            self.state.undo_stack.append(snapshot)
            self.state.redo_stack.clear()
            self._refresh_commits()
        except GitCommandError as exc:
            self.state.status = str(exc)

    def _merge(self) -> None:
        ref = self._prompt("Merge which branch/ref into current?", default="origin/main")
        if not ref:
            return
        preview = self.git.merge_preview(ref)
        if not self._confirm(f"Apply merge for {ref}?\n\nPreview:\n{preview[:200]}..."):
            return
        snapshot = self.git.snapshot_head()
        try:
            output = self.git.merge(ref)
            self.state.status = output.splitlines()[0] if output else f"Merged {ref}"
            self.state.undo_stack.append(snapshot)
            self.state.redo_stack.clear()
            self._refresh_commits()
        except GitCommandError as exc:
            self.state.status = str(exc)

    def _stash_worktree(self) -> None:
        if not self._confirm("Stash current working tree?"):
            return
        try:
            message = self.git.stash()
            self.state.status = message.strip() or "Working tree stashed."
        except GitCommandError as exc:
            self.state.status = str(exc)

    def _undo(self) -> None:
        if not self.state.undo_stack:
            self.state.status = "Undo stack empty."
            return
        snapshot = self.state.undo_stack.pop()
        redo = self.git.snapshot_head()
        try:
            self.git.restore_snapshot(snapshot)
            self.state.redo_stack.append(redo)
            self.state.status = "Undo complete."
            self._refresh_commits()
        except GitCommandError as exc:
            self.state.status = str(exc)

    def _redo(self) -> None:
        if not self.state.redo_stack:
            self.state.status = "Redo stack empty."
            return
        snapshot = self.state.redo_stack.pop()
        undo = self.git.snapshot_head()
        try:
            self.git.restore_snapshot(snapshot)
            self.state.undo_stack.append(undo)
            self.state.status = "Redo complete."
            self._refresh_commits()
        except GitCommandError as exc:
            self.state.status = str(exc)

    # --------------------------------------------------------------- rebase mode
    def _open_rebase_planner(self) -> None:
        entries = self.git.build_rebase_todo(5)
        if len(entries) <= 1:
            self.state.status = "Not enough commits for rebase."
            return
        entries.reverse()  # show oldest first
        self.state.rebase_entries = [RebaseEntry(commit=commit) for commit in entries]
        self.state.rebase_cursor = 0
        self.state.view = "rebase"
        self.state.status = "Interactive rebase planner ready."

    def _handle_rebase_key(self, key: int) -> bool:
        if key == 27:  # ESC
            self.state.view = "diff"
            self.state.rebase_entries.clear()
            return True
        if key in (curses.KEY_UP, ord("k")):
            self.state.rebase_cursor = max(0, self.state.rebase_cursor - 1)
            return True
        if key in (curses.KEY_DOWN, ord("j")):
            self.state.rebase_cursor = min(len(self.state.rebase_entries) - 1, self.state.rebase_cursor + 1)
            return True
        if key in (ord("p"), ord("s"), ord("f"), ord("e"), ord("r"), ord("x")):
            mapping = {
                ord("p"): "pick",
                ord("s"): "squash",
                ord("f"): "fixup",
                ord("e"): "edit",
                ord("r"): "reword",
                ord("x"): "drop",
            }
            self.state.rebase_entries[self.state.rebase_cursor].action = mapping[key]
            return True
        if key in (10, 13):
            self._launch_rebase()
            return True
        return True

    def _launch_rebase(self) -> None:
        actions = [(entry.action, entry.commit) for entry in self.state.rebase_entries]
        if not self._confirm("Execute interactive rebase with current plan?"):
            return
        snapshot = self.git.snapshot_head()
        try:
            self.git.run_interactive_rebase(actions)
            self.state.undo_stack.append(snapshot)
            self.state.redo_stack.clear()
            self.state.status = "Rebase completed."
            self.state.view = "diff"
            self._refresh_commits()
        except GitCommandError as exc:
            self.state.status = str(exc)

    # ------------------------------------------------------------- plugin panel
    def _handle_plugin_key(self, key: int) -> bool:
        if key in (curses.KEY_UP, ord("k")):
            self.state.plugin_index = max(0, self.state.plugin_index - 1)
            return True
        if key in (curses.KEY_DOWN, ord("j")):
            self.state.plugin_index = min(len(self.plugins) - 1, self.state.plugin_index + 1)
            return True
        if key in (10, 13):
            plugin = self.plugins[self.state.plugin_index]
            try:
                output = plugin.run(self.git, self)
            except Exception as exc:  # pragma: no cover - defensive
                output = f"Plugin {plugin.name} failed: {exc}"
            self.state.plugin_output = output
            self.state.status = f"Plugin {plugin.name} executed."
            return True
        if key == 27:  # ESC
            self.state.view = "diff"
            return True
        return True

    # -------------------------------------------------------------- danger keys
    def _handle_danger_key(self, key: int) -> bool:
        if key == 27:
            self.state.danger_mode = False
            self.state.view = "diff"
            return True
        if key in (ord("r"), ord("R")):
            commit = self.state.commits[self.state.selected]
            if not self._confirm(f"Hard reset to {commit.short_hash}? This cannot be undone!"):
                return True
            snapshot = self.git.snapshot_head()
            try:
                self.git.rollback_hard(commit.hash)
                self.state.status = f"Rolled back to {commit.short_hash}."
                self.state.undo_stack.append(snapshot)
                self.state.redo_stack.clear()
                self._refresh_commits()
            except GitCommandError as exc:
                self.state.status = str(exc)
            return True
        if key in (ord("p"), ord("P")):
            branch = self.git.current_branch()
            if not branch:
                self.state.status = "Cannot force push detached HEAD."
                return True
            if not self._confirm(f"Force push {branch}? Animated skull approves?"):
                return True
            snapshot = self.git.snapshot_head()
            try:
                message = self.git.force_push(branch)
                self.state.status = message.splitlines()[0] if message else f"Force pushed {branch}."
                self.state.undo_stack.append(snapshot)
                self.state.redo_stack.clear()
            except GitCommandError as exc:
                self.state.status = str(exc)
            return True
        if key in (ord("s"), ord("S")):
            self._stash_worktree()
            return True
        return True

    # ---------------------------------------------------------- helper methods
    def _refresh_commits(self) -> None:
        self.state.commits = self.git.list_commits()
        self.state.selected = min(self.state.selected, len(self.state.commits) - 1)
        self.diff_cache.clear()

    def _cycle_github_tab(self, delta: int) -> None:
        idx = GITHUB_TABS.index(self.state.github_tab)
        idx = (idx + delta) % len(GITHUB_TABS)
        self.state.github_tab = GITHUB_TABS[idx]
        self._ensure_github_data(self.state.github_tab)
        self.state.status = f"Viewing GitHub {self.state.github_tab}."

    def _search(self) -> None:
        query = self._prompt("Search commits or #number:")
        if not query:
            return
        if query.startswith("#") and query[1:].isdigit() and self.github:
            number = int(query[1:])
            try:
                item = self.github.lookup_issue_or_pr(number)
                lines = [
                    f"#{item.number} [{item.type}] {item.title}",
                    f"State: {item.state}",
                    f"Author: {item.author}",
                    item.url,
                ]
                self.state.plugin_output = "\n".join(lines)
                self.state.view = "github"
                self.state.status = f"Loaded GitHub item #{number}."
                return
            except GitHubUnavailable as exc:
                self.state.status = str(exc)
                return
        # Fallback to commit search
        for idx, commit in enumerate(self.state.commits):
            if query.lower() in commit.subject.lower() or query.lower() in commit.short_hash.lower():
                self.state.selected = idx
                self.state.view = "diff"
                self.state.status = f"Jumped to {commit.short_hash}"
                return
        self.state.status = "No matches found."

    def _prompt(self, prompt: str, default: str = "") -> str:
        max_y, max_x = self.stdscr.getmaxyx()
        width = max(len(prompt) + 20, 40)
        win = curses.newwin(5, width, max_y // 2 - 2, max_x // 2 - width // 2)
        win.bkgd(" ", curses.color_pair(self.colors["panel"]))
        win.box()
        win.addstr(1, 2, prompt)
        win.addstr(2, 2, default)
        curses.echo()
        win.refresh()
        try:
            value = win.getstr(2, 2 + len(default), width - 4 - len(default)).decode()
        finally:
            curses.noecho()
        return value or default

    def _confirm(self, prompt: str) -> bool:
        max_y, max_x = self.stdscr.getmaxyx()
        width = min(max(len(prompt) + 6, 40), max_x - 4)
        win = curses.newwin(5, width, max_y // 2 - 2, max_x // 2 - width // 2)
        win.bkgd(" ", curses.color_pair(self.colors["panel"]))
        win.box()
        wrapped = self._wrap_text(prompt, width - 4)
        for idx, line in enumerate(wrapped[:2]):
            win.addstr(1 + idx, 2, line)
        win.addstr(3, 2, "[y]es / [n]o?")
        win.refresh()
        while True:
            ch = win.getch()
            if ch in (ord("y"), ord("Y")):
                return True
            if ch in (ord("n"), ord("N"), 27):
                return False

    def _wrap_text(self, text: str, width: int) -> List[str]:
        words = text.split()
        lines: List[str] = []
        current: List[str] = []
        length = 0
        for word in words:
            if length + len(word) + 1 > width and current:
                lines.append(" ".join(current))
                current = [word]
                length = len(word) + 1
            else:
                current.append(word)
                length += len(word) + 1
        if current:
            lines.append(" ".join(current))
        return lines


def run() -> None:
    curses.wrapper(lambda stdscr: NeonGitApp(stdscr).run())
