"""Interactive command line interface for gitHelper."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from . import __version__
from .console import (
    banner,
    bullet_list,
    confirm,
    error,
    info,
    prompt,
    prompt_secret,
    rule,
    success,
    warning,
)
from .directory import RepositoryDirectoryManager
from .errors import DirectoryError, SSHKeyError
from .git import GitRepository, GitRepositoryError
from .ssh import SSHKeyManager

__all__ = ["GitHelperApp", "main"]


class GitHelperApp:
    """Simple interactive workflow for managing git helper tasks."""

    def __init__(self) -> None:
        self.repo_manager = RepositoryDirectoryManager()
        self.ssh_manager = SSHKeyManager()
        self.active_repository: Optional[Path] = None

    # ----------------------------------------------------------------- utilities
    def _show_header(self, title: str) -> None:
        banner(f"gitHelper • {title}")
        info(f"Version {__version__}")
        rule()

    def _show_current_directory(self) -> None:
        try:
            current = self.repo_manager.current_directory()
        except DirectoryError as exc:
            warning(str(exc))
        else:
            info(f"Active repository directory: {current}")

    def _show_current_repository(self) -> None:
        if not self.active_repository:
            info("Active repository: none selected. Use the git workflow menu to choose one.")
            return
        repo = GitRepository(self.active_repository)
        state = "initialised" if repo.is_repository else "not initialised"
        info(f"Active repository: {self.active_repository} ({state})")

    def _show_help(self, topic: str = "main") -> None:
        topics = {
            "main": [
                "Use the numbered options or their shortcuts (e.g. 'ssh') to navigate.",
                "Configure the workspace directory before working with repositories.",
                "Visit the Git repository workflow to initialise repos and run commits.",
                "An active repository is remembered between actions; select it once and reuse it.",
                "Type '?' or 'help' on any screen to see context-aware tips.",
            ],
            "directory": [
                "Change repository directory updates the stored workspace path.",
                "Refresh reloads configuration from disk in case it was edited manually.",
                "Use full paths or paths relative to your home directory when prompted.",
            ],
            "ssh": [
                "Generate creates a new Ed25519 key pair inside ~/.ssh by default.",
                "Import copies an existing private key into ~/.ssh and can add it to ssh-agent.",
                "Add to agent allows any key to be loaded into the current ssh-agent session.",
            ],
            "repository": [
                "Select repository chooses which project subsequent Git actions will use.",
                "Initialise can create a brand new repository anywhere on disk and optionally add a remote.",
                "Stage all runs 'git add --all' for the active repository.",
                "Commit prompts for a message and performs 'git commit'.",
                "Push and Pull wrap the respective Git commands and offer sensible defaults.",
                "Configure remote adds or updates the URL for remotes such as 'origin'.",
            ],
        }
        self._show_header("Help")
        bullet_list(topics.get(topic, topics["main"]))
        info("Press Enter to return to the previous menu.")
        input()

    # -------------------------------------------------------------- main menus
    def run(self) -> None:
        """Launch the application loop."""

        while True:
            self._show_header("Control Centre")
            self._show_current_directory()
            self._show_current_repository()
            info("Choose an operation:")
            bullet_list(
                [
                    "[1] Manage repository directory",
                    "[2] View repositories in current directory",
                    "[3] SSH key management",
                    "[4] Git repository workflow",
                    "[Q] Quit",
                ]
            )
            choice = prompt("Select an option").strip().lower()
            if choice in {"1", "directory", "d"}:
                self._directory_menu()
            elif choice in {"2", "repos", "r"}:
                self._list_repositories()
            elif choice in {"3", "ssh"}:
                self._ssh_menu()
            elif choice in {"4", "git", "g"}:
                self._repository_menu()
            elif choice in {"?", "h", "help"}:
                self._show_help("main")
            elif choice in {"q", "quit"}:
                success("Thanks for using gitHelper. Goodbye!")
                return
            else:
                warning("Unknown option. Please select one of the listed commands.")

    # ----------------------------------------------------------- directory menu
    def _directory_menu(self) -> None:
        while True:
            self._show_header("Repository directory")
            self._show_current_directory()
            bullet_list(
                [
                    "[1] Change repository directory",
                    "[2] Refresh directory configuration",
                    "[B] Back to main menu",
                ]
            )
            choice = prompt("Select an option").strip().lower()
            if choice in {"1", "change", "c"}:
                self._change_directory()
            elif choice in {"2", "refresh"}:
                self.repo_manager.refresh()
                success("Configuration reloaded.")
            elif choice in {"?", "h", "help"}:
                self._show_help("directory")
            elif choice in {"b", "back"}:
                return
            else:
                warning("Unknown option. Please select one of the listed commands.")

    def _change_directory(self) -> None:
        new_dir = prompt("Enter the new repository directory").strip()
        if not new_dir:
            warning("No directory provided; nothing changed.")
            return
        path = Path(new_dir).expanduser()
        create = False
        if not path.exists():
            create = confirm(
                f"{path} does not exist. Create it now?",
                default=True,
            )
        try:
            updated = self.repo_manager.change_directory(path, create=create)
        except DirectoryError as exc:
            error(str(exc))
        else:
            success(f"Repository directory updated to {updated}")

    def _list_repositories(self) -> None:
        try:
            repositories = self.repo_manager.list_repositories()
        except DirectoryError as exc:
            error(str(exc))
            return
        if not repositories:
            warning("No Git repositories found in the configured directory.")
            return
        success(f"Found {len(repositories)} repository(ies):")
        bullet_list([repo.name for repo in repositories])

    # -------------------------------------------------------------- SSH actions
    def _ssh_menu(self) -> None:
        while True:
            self._show_header("SSH key management")
            bullet_list(
                [
                    "[1] Generate new SSH key",
                    "[2] Import existing SSH key",
                    "[3] Add SSH key to agent",
                    "[B] Back to main menu",
                ]
            )
            choice = prompt("Select an option").strip().lower()
            if choice in {"1", "generate", "g"}:
                self._generate_key()
            elif choice in {"2", "import", "i"}:
                self._import_key()
            elif choice in {"3", "agent", "a"}:
                self._add_key_to_agent()
            elif choice in {"?", "h", "help"}:
                self._show_help("ssh")
            elif choice in {"b", "back"}:
                return
            else:
                warning("Unknown option. Please select one of the listed commands.")

    def _generate_key(self) -> None:
        email = prompt("Email address for the SSH key").strip()
        key_name = prompt("Filename for the key", default="id_ed25519").strip() or "id_ed25519"
        passphrase = prompt_secret("Passphrase (leave empty for none)")
        overwrite = False
        target = self.ssh_manager.ssh_dir / key_name
        if target.exists():
            overwrite = confirm(
                f"{target} already exists. Replace it?",
                default=False,
            )
        try:
            private_key = self.ssh_manager.generate_key(
                email=email,
                key_name=key_name,
                passphrase=passphrase,
                overwrite=overwrite,
            )
        except SSHKeyError as exc:
            error(str(exc))
            return
        success(f"Generated SSH key: {private_key}")
        public_key = private_key.with_suffix(".pub")
        if public_key.exists():
            info(f"Public key saved at {public_key}")
            info("Add this key to your Git hosting provider as needed.")

    def _import_key(self) -> None:
        source = prompt("Path to the existing private key").strip()
        if not source:
            warning("No key path supplied.")
            return
        name = prompt("Save the key as", default=Path(source).name).strip()
        add = confirm("Add the key to the SSH agent after importing?", default=True)
        try:
            destination = self.ssh_manager.import_key(source, name=name or None, add_to_agent=add)
        except SSHKeyError as exc:
            error(str(exc))
            return
        success(f"Key imported to {destination}")
        if add:
            success("Key added to ssh-agent.")

    def _add_key_to_agent(self) -> None:
        key_path = prompt("Path to the private key to add to ssh-agent").strip()
        if not key_path:
            warning("No key path supplied.")
            return
        try:
            output = self.ssh_manager.add_to_agent(key_path)
        except SSHKeyError as exc:
            error(str(exc))
        else:
            success("Key added to ssh-agent.")
            if output:
                info(output)

    # ------------------------------------------------------------- git actions
    def _require_repository(self, *, allow_uninitialised: bool = False) -> GitRepository | None:
        if not self.active_repository:
            warning("No active repository selected. Choose 'Select repository' first.")
            return None
        repo = GitRepository(self.active_repository)
        if not repo.exists:
            warning(f"{self.active_repository} does not exist. Initialise it first.")
            return None
        if not allow_uninitialised and not repo.is_repository:
            warning(
                f"{self.active_repository} is not a Git repository. Choose 'Initialise new repository' to set it up."
            )
            return None
        return repo

    def _repository_menu(self) -> None:
        while True:
            self._show_header("Git repository workflow")
            self._show_current_repository()
            bullet_list(
                [
                    "[1] Select repository",
                    "[2] Initialise new repository",
                    "[3] Show status",
                    "[4] Stage all changes",
                    "[5] Commit staged changes",
                    "[6] Push to remote",
                    "[7] Pull from remote",
                    "[8] Configure remote",
                    "[B] Back to main menu",
                ]
            )
            choice = prompt("Select an option").strip().lower()
            if choice in {"1", "select", "s"}:
                self._select_repository()
            elif choice in {"2", "init", "i"}:
                self._initialise_repository()
            elif choice in {"3", "status"}:
                self._show_status()
            elif choice in {"4", "stage", "a"}:
                self._stage_all()
            elif choice in {"5", "commit", "c"}:
                self._commit_changes()
            elif choice in {"6", "push", "p"}:
                self._push_changes()
            elif choice in {"7", "pull", "l"}:
                self._pull_changes()
            elif choice in {"8", "remote", "r"}:
                self._configure_remote()
            elif choice in {"?", "h", "help"}:
                self._show_help("repository")
            elif choice in {"b", "back"}:
                return
            else:
                warning("Unknown option. Please select one of the listed commands.")

    def _select_repository(self) -> None:
        try:
            repositories = self.repo_manager.list_repositories()
        except DirectoryError as exc:
            error(str(exc))
            repositories = []

        if repositories:
            info("Repositories discovered in the configured directory:")
            items = [f"[{idx + 1}] {repo}" for idx, repo in enumerate(repositories)]
            bullet_list(items)
            default = "1" if len(repositories) == 1 else ""
            response = prompt(
                "Enter the number of the repository to use or provide a custom path",
                default=default,
            )
        else:
            warning("No repositories detected. Enter a path manually.")
            response = prompt("Repository path")

        if not response.strip():
            warning("No repository selected.")
            return

        selected_path: Path
        if response.isdigit() and repositories:
            index = int(response) - 1
            if not 0 <= index < len(repositories):
                warning("Selection out of range.")
                return
            selected_path = repositories[index]
        else:
            selected_path = Path(response).expanduser()

        self.active_repository = selected_path
        repo = GitRepository(selected_path)
        if repo.is_repository:
            success(f"Active repository set to {selected_path}")
        else:
            warning(
                f"{selected_path} is not initialised yet. Choose 'Initialise new repository' before running Git commands."
            )

    def _initialise_repository(self) -> None:
        default_path: str | None = None
        if self.active_repository:
            default_path = str(self.active_repository)
        else:
            try:
                default_path = str(self.repo_manager.current_directory())
            except DirectoryError:
                default_path = None

        target_input = prompt("Directory to initialise", default=default_path).strip()
        if not target_input:
            warning("No directory supplied; cancelled initialisation.")
            return

        target = Path(target_input).expanduser()
        repo = GitRepository(target)
        if target.exists() and not target.is_dir():
            error(f"{target} exists but is not a directory.")
            return
        if not target.exists():
            create = confirm(f"{target} does not exist. Create it?", default=True)
            if not create:
                warning("Initialisation aborted.")
                return

        default_branch = prompt("Initial branch name", default="main").strip()
        try:
            output = repo.init(default_branch=default_branch or None)
        except GitRepositoryError as exc:
            error(str(exc))
            return

        self.active_repository = target
        success(f"Initialised Git repository in {target}")
        if output:
            info(output)

        remote_url = prompt("Remote URL to add (leave empty to skip)").strip()
        if remote_url:
            try:
                remote_output = repo.set_remote("origin", remote_url, replace=True)
            except GitRepositoryError as exc:
                error(str(exc))
            else:
                info(remote_output or "Remote 'origin' updated.")

    def _show_status(self) -> None:
        repo = self._require_repository()
        if not repo:
            return
        try:
            output = repo.status()
        except GitRepositoryError as exc:
            error(str(exc))
            return
        info("Repository status:")
        if output:
            for line in output.splitlines():
                print(line)

    def _stage_all(self) -> None:
        repo = self._require_repository()
        if not repo:
            return
        try:
            repo.stage_all()
        except GitRepositoryError as exc:
            error(str(exc))
        else:
            success("All changes staged.")

    def _commit_changes(self) -> None:
        repo = self._require_repository()
        if not repo:
            return
        message = prompt("Commit message").strip()
        if not message:
            warning("Commit message is required.")
            return
        try:
            output = repo.commit(message)
        except GitRepositoryError as exc:
            error(str(exc))
        else:
            success("Commit created successfully.")
            if output:
                info(output)

    def _push_changes(self) -> None:
        repo = self._require_repository()
        if not repo:
            return
        default_remote = "origin"
        current_branch = repo.current_branch()
        remote = prompt("Remote to push to", default=default_remote).strip() or default_remote
        branch = prompt("Branch to push", default=current_branch or "").strip()
        if not branch:
            warning("Branch name is required to push.")
            return
        tracking = repo.tracking_branch()
        set_upstream_default = tracking is None
        if set_upstream_default:
            info("No upstream configured for this branch. An upstream will be set during push.")
        set_upstream = confirm(
            "Set upstream while pushing?",
            default=set_upstream_default,
        )
        try:
            output = repo.push(remote, branch, set_upstream=set_upstream)
        except GitRepositoryError as exc:
            error(str(exc))
        else:
            success("Push completed successfully.")
            if output:
                info(output)

    def _pull_changes(self) -> None:
        repo = self._require_repository()
        if not repo:
            return
        default_remote = "origin"
        current_branch = repo.current_branch()
        if not current_branch:
            warning("Cannot pull while in a detached HEAD state.")
            return
        remote = prompt("Remote to pull from", default=default_remote).strip() or default_remote
        branch = prompt("Branch to pull", default=current_branch).strip()
        if not branch:
            warning("Branch name is required to pull.")
            return
        try:
            output = repo.pull(remote, branch)
        except GitRepositoryError as exc:
            error(str(exc))
        else:
            success("Pull completed successfully.")
            if output:
                info(output)

    def _configure_remote(self) -> None:
        repo = self._require_repository()
        if not repo:
            return
        remote_name = prompt("Remote name", default="origin").strip() or "origin"
        remote_url = prompt("Remote URL").strip()
        if not remote_url:
            warning("Remote URL is required.")
            return
        replace = repo.remote_exists(remote_name)
        if replace:
            replace = confirm(
                f"Remote '{remote_name}' already exists. Update its URL?",
                default=True,
            )
            if not replace:
                warning("Remote update cancelled.")
                return
        try:
            output = repo.set_remote(remote_name, remote_url, replace=True)
        except GitRepositoryError as exc:
            error(str(exc))
        else:
            success(f"Remote '{remote_name}' configured.")
            if output:
                info(output)


def main() -> None:
    """Entry point used by ``python -m git_helper``."""

    app = GitHelperApp()
    app.run()
