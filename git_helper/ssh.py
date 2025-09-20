"""SSH key management helpers."""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
from pathlib import Path
from typing import Optional

from .errors import SSHKeyError

__all__ = ["SSHKeyManager"]


class SSHKeyManager:
    """High level helpers for SSH key management."""

    def __init__(self, ssh_dir: Path | None = None) -> None:
        self.ssh_dir = Path(ssh_dir or Path.home() / ".ssh").expanduser()

    # ----------------------------------------------------------------- utilities
    def _ensure_dir(self) -> None:
        try:
            self.ssh_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        except OSError as exc:  # pragma: no cover - platform specific
            raise SSHKeyError(f"Unable to create SSH directory {self.ssh_dir}: {exc}")

    def _run(self, *command: str) -> subprocess.CompletedProcess:
        try:
            result = subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
            )
        except FileNotFoundError as exc:
            raise SSHKeyError(
                f"Required command '{command[0]}' is not available on PATH."
            ) from exc
        except subprocess.CalledProcessError as exc:
            raise SSHKeyError(exc.stderr.strip() or exc.stdout.strip() or str(exc)) from exc
        return result

    # --------------------------------------------------------------- key actions
    def generate_key(
        self,
        *,
        email: str,
        key_name: str = "id_ed25519",
        passphrase: str = "",
        overwrite: bool = False,
    ) -> Path:
        """Generate a new SSH key pair and return the path to the private key."""

        if not email.strip():
            raise SSHKeyError("An email address is required to generate a key.")

        self._ensure_dir()
        private_key = self.ssh_dir / key_name
        if private_key.exists() and not overwrite:
            raise SSHKeyError(
                f"Key {private_key} already exists. Use overwrite=True to replace it."
            )

        command = (
            "ssh-keygen",
            "-t",
            "ed25519",
            "-C",
            email,
            "-f",
            str(private_key),
            "-N",
            passphrase,
        )
        self._run(*command)

        os.chmod(private_key, stat.S_IRUSR | stat.S_IWUSR)
        public_key = private_key.with_suffix(".pub")
        if public_key.exists():
            os.chmod(public_key, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
        return private_key

    def add_to_agent(self, key_path: str | Path) -> str:
        """Add an SSH key to the running ssh-agent and return its output."""

        path = Path(key_path).expanduser()
        if not path.exists():
            raise SSHKeyError(f"Key {path} does not exist.")
        if not path.is_file():
            raise SSHKeyError(f"{path} is not a file.")
        result = self._run("ssh-add", str(path))
        return result.stdout.strip() or result.stderr.strip()

    def import_key(
        self,
        source: str | Path,
        *,
        name: Optional[str] = None,
        add_to_agent: bool = False,
    ) -> Path:
        """Copy an existing key into the SSH directory.

        The private (and if present public) key will be copied. When
        ``add_to_agent`` is ``True`` the imported key is automatically added to
        the ssh-agent.
        """

        source_path = Path(source).expanduser()
        if not source_path.exists():
            raise SSHKeyError(f"Key {source_path} does not exist.")
        if not source_path.is_file():
            raise SSHKeyError(f"{source_path} is not a valid private key file.")

        self._ensure_dir()
        target_name = name or source_path.name
        destination = self.ssh_dir / target_name
        if destination.exists():
            raise SSHKeyError(f"Destination key {destination} already exists.")

        try:
            shutil.copy2(source_path, destination)
        except OSError as exc:  # pragma: no cover - platform specific
            raise SSHKeyError(f"Unable to copy key to {destination}: {exc}") from exc
        os.chmod(destination, stat.S_IRUSR | stat.S_IWUSR)

        source_public = source_path.with_suffix(".pub")
        if source_public.exists():
            destination_public = destination.with_suffix(".pub")
            try:
                shutil.copy2(source_public, destination_public)
            except OSError as exc:  # pragma: no cover - platform specific
                raise SSHKeyError(
                    f"Unable to copy public key to {destination_public}: {exc}"
                ) from exc
            os.chmod(
                destination_public,
                stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH,
            )

        if add_to_agent:
            self.add_to_agent(destination)
        return destination
