"""Custom exceptions used throughout the gitHelper package."""

from __future__ import annotations

__all__ = [
    "GitHelperError",
    "DirectoryError",
    "SSHKeyError",
]


class GitHelperError(RuntimeError):
    """Base class for package specific exceptions."""


class DirectoryError(GitHelperError):
    """Raised when repository directory operations fail."""


class SSHKeyError(GitHelperError):
    """Raised when SSH key management operations fail."""
