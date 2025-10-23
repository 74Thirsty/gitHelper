"""Convenience façade around :mod:`git_helper.ssh` for UI layers."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from .ssh import SSHKeyManager

__all__ = ["SSHTools"]


class SSHTools:
    """Expose SSH key operations for GUI/CLI frontends."""

    def __init__(self, ssh_dir: Path | None = None) -> None:
        self.manager = SSHKeyManager(ssh_dir)

    def generate(self, *, email: str, key_name: str = "id_ed25519", passphrase: str = "",
                 overwrite: bool = False) -> Path:
        return self.manager.generate_key(
            email=email,
            key_name=key_name,
            passphrase=passphrase,
            overwrite=overwrite,
        )

    def add_to_agent(self, key_path: str | Path) -> str:
        return self.manager.add_to_agent(key_path)

    def import_key(self, source: str | Path, *, name: Optional[str] = None,
                   add_to_agent: bool = False) -> Path:
        return self.manager.import_key(source, name=name, add_to_agent=add_to_agent)

    def list_keys(self) -> list[Path]:
        directory = self.manager.ssh_dir
        if not directory.exists():
            return []
        keys: list[Path] = []
        for entry in directory.glob("id_*"):
            if entry.suffix == ".pub":
                continue
            if entry.is_file():
                keys.append(entry)
        return sorted(keys)

