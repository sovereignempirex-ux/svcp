import pytest

from scvp.core.config import load_config
from scvp.core.exceptions import ConfigError


def test_defaults():
    config = load_config()
    assert config.get("model.provider") == "mock"
    assert config.get("app.env") == "development"


def test_env_override(monkeypatch):
    monkeypatch.setenv("SCVP_MODEL__PROVIDER", "openai")
    config = load_config()
    assert config.get("model.provider") == "openai"


def test_missing_key_returns_default():
    config = load_config()
    assert config.get("does.not.exist", "fallback") == "fallback"


def test_require_raises_on_missing():
    config = load_config()
    with pytest.raises(ConfigError):
        config.require("does.not.exist")


def test_explicit_overrides_win_over_everything(monkeypatch):
    monkeypatch.setenv("SCVP_MODEL__PROVIDER", "openai")
    config = load_config(overrides={"model": {"provider": "anthropic"}})
    assert config.get("model.provider") == "anthropic"
