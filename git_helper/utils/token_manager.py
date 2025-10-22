"""Secure token management backed by keyring."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence

try:  # pragma: no cover - optional dependency
    import keyring
except ModuleNotFoundError:  # pragma: no cover
    class _FallbackKeyring:
        """Minimal in-memory keyring used when the real backend is unavailable."""

        _storage: dict[tuple[str, str], str] = {}

        @classmethod
        def set_password(cls, service: str, user: str, password: str) -> None:
            cls._storage[(service, user)] = password

        @classmethod
        def get_password(cls, service: str, user: str) -> str | None:
            return cls._storage.get((service, user))

        @classmethod
        def delete_password(cls, service: str, user: str) -> None:
            cls._storage.pop((service, user), None)

    keyring = _FallbackKeyring()  # type: ignore

from ..errors import GitHelperError

SERVICE_NAME = "githelper"

__all__ = ["TokenManager", "TokenManagerError", "SERVICE_NAME"]


class TokenManagerError(GitHelperError):
    """Raised when token operations fail."""


@dataclass
class TokenManager:
    """Manage GitHub tokens stored in the system keyring."""

    username: str = "default"

    def _credential_id(self) -> str:
        return f"{self.username}:gh-pat"

    def save(self, token: str) -> None:
        if not token:
            raise TokenManagerError("Token cannot be empty")
        keyring.set_password(SERVICE_NAME, self._credential_id(), token)

    def load(self) -> str | None:
        return keyring.get_password(SERVICE_NAME, self._credential_id())

    def delete(self) -> None:
        keyring.delete_password(SERVICE_NAME, self._credential_id())

    def require(self, scopes: Sequence[str] | None = None, scope_provider: Callable[[], Sequence[str]] | None = None) -> str:
        token = self.load()
        if not token:
            raise TokenManagerError("No GitHub token is available. Run 'git-helper onboard' to configure one.")
        if scopes:
            available = set()
            if scope_provider:
                available.update(scope_provider())
            missing = [scope for scope in scopes if scope not in available]
            if missing:
                raise TokenManagerError(
                    "GitHub token is missing required scopes: " + ", ".join(missing)
                )
        return token

    def describe(self, scope_provider: Callable[[], Sequence[str]] | None = None) -> str:
        token = self.load()
        if not token:
            return "No GitHub token configured."
        scopes = []
        if scope_provider:
            try:
                scopes = list(scope_provider())
            except Exception:  # pragma: no cover - defensive
                scopes = []
        if scopes:
            scope_text = ", ".join(sorted(scopes))
        else:
            scope_text = "unknown scopes"
        return f"Token stored for '{self.username}' with {scope_text}."
