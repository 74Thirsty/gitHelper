from __future__ import annotations

import pytest

from git_helper.utils.token_manager import TokenManager, TokenManagerError


@pytest.fixture()
def fake_keyring(monkeypatch):
    storage = {}

    def set_password(service, user, password):
        storage[(service, user)] = password

    def get_password(service, user):
        return storage.get((service, user))

    def delete_password(service, user):
        storage.pop((service, user), None)

    monkeypatch.setattr("git_helper.utils.token_manager.keyring.set_password", set_password)
    monkeypatch.setattr("git_helper.utils.token_manager.keyring.get_password", get_password)
    monkeypatch.setattr("git_helper.utils.token_manager.keyring.delete_password", delete_password)
    return storage


def test_token_manager_store_and_require(fake_keyring):
    manager = TokenManager(username="tester")
    manager.save("ghp_secret")
    assert manager.load() == "ghp_secret"
    scope_provider = lambda: ["repo", "workflow"]
    assert manager.require(scopes=["repo"], scope_provider=scope_provider) == "ghp_secret"
    with pytest.raises(TokenManagerError):
        manager.require(scopes=["admin:org"], scope_provider=scope_provider)
    description = manager.describe(scope_provider=scope_provider)
    assert "repo" in description
    manager.delete()
    assert manager.load() is None
    with pytest.raises(TokenManagerError):
        manager.require(scopes=["repo"], scope_provider=scope_provider)
