"""Interactive command line interface for gitHelper."""

from __future__ import annotations

from pathlib import Path

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
from .ssh import SSHKeyManager

__all__ = ["GitHelperApp", "main"]


class GitHelperApp:
    """Simple interactive workflow for managing git helper tasks."""

    def __init__(self) -> None:
        self.repo_manager = RepositoryDirectoryManager()
        self.ssh_manager = SSHKeyManager()

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

    # -------------------------------------------------------------- main menus
    def run(self) -> None:
        """Launch the application loop."""

        while True:
            self._show_header("Control Centre")
            self._show_current_directory()
            info("Choose an operation:")
            bullet_list(
                [
                    "[1] Manage repository directory",
                    "[2] View repositories in current directory",
                    "[3] SSH key management",
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


def main() -> None:
    """Entry point used by ``python -m git_helper``."""

    app = GitHelperApp()
    app.run()
