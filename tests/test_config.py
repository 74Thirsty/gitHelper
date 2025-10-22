from __future__ import annotations

from git_helper.utils.config import ConfigManager


def test_config_manager_creates_defaults(tmp_path):
    config_dir = tmp_path / "config"
    config_file = config_dir / "config.toml"
    manager = ConfigManager(path=config_file)
    assert manager.get("github", "default_org") == ""
    assert manager.get("ui", "use_gui") is False
    manager.set("github", "default_org", "octo-org")
    manager.set("ui", "theme", "dark")

    manager.reload()
    assert manager.get("github", "default_org") == "octo-org"
    assert manager.get("ui", "theme") == "dark"
    summary = manager.profile_summary()
    assert "octo-org" in summary
    assert "dark" in summary
