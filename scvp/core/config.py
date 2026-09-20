"""
SCVP Configuration System
===========================
Loads configuration from, in increasing order of precedence:

    1. built-in defaults
    2. a config file (scvp.config.yaml / scvp.config.yml / scvp.config.json),
       if present
    3. environment variables (SCVP_ prefixed, "__" = nesting separator)
    4. values passed explicitly to `load_config(overrides=...)`

No secret is ever read from the config file. API keys and other
secrets are only ever read from environment variables -- never
written into a config file that could be committed to git.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from scvp.core.exceptions import ConfigError

_DEFAULTS: Dict[str, Any] = {
    "app": {
        "name": "scvp-app",
        "env": "development",
    },
    "model": {
        "provider": "mock",
        "name": "scvp-mock-1",
    },
    "models": {
        "default": "mock",
        "providers": {},
    },
    "logging": {
        "level": "INFO",
        "json": True,
    },
}

_ENV_PREFIX = "SCVP_"
_CONFIG_FILENAMES = ("scvp.config.yaml", "scvp.config.yml", "scvp.config.json")


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    result = dict(base)
    for key, value in override.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _find_config_file(start: Optional[Path] = None) -> Optional[Path]:
    directory = start or Path.cwd()
    for filename in _CONFIG_FILENAMES:
        candidate = directory / filename
        if candidate.is_file():
            return candidate
    return None


def _load_file(path: Path) -> Dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigError(f"Could not read config file '{path}': {exc}") from exc

    try:
        if path.suffix in (".yaml", ".yml"):
            data = yaml.safe_load(text) or {}
        else:
            data = json.loads(text)
    except (yaml.YAMLError, json.JSONDecodeError) as exc:
        raise ConfigError(f"Could not parse config file '{path}': {exc}") from exc

    if not isinstance(data, dict):
        raise ConfigError(f"Config file '{path}' must contain a top-level mapping.")
    return data


def _load_env_overrides(prefix: str = _ENV_PREFIX) -> Dict[str, Any]:
    """
    Turns SCVP_MODEL__PROVIDER=openai into {"model": {"provider": "openai"}}.
    Double underscore `__` is the nesting separator.
    """
    overrides: Dict[str, Any] = {}
    for env_key, env_value in os.environ.items():
        if not env_key.startswith(prefix):
            continue
        path = env_key[len(prefix):].lower().split("__")
        cursor = overrides
        for part in path[:-1]:
            cursor = cursor.setdefault(part, {})
        cursor[path[-1]] = env_value
    return overrides


class SCVPConfig:
    """Read-only, dot-path accessible configuration object."""

    def __init__(self, data: Dict[str, Any]):
        self._data = data

    def get(self, dotted_key: str, default: Any = None) -> Any:
        cursor: Any = self._data
        for part in dotted_key.split("."):
            if isinstance(cursor, dict) and part in cursor:
                cursor = cursor[part]
            else:
                return default
        return cursor

    def require(self, dotted_key: str) -> Any:
        sentinel = object()
        value = self.get(dotted_key, sentinel)
        if value is sentinel:
            raise ConfigError(f"Missing required config key: '{dotted_key}'")
        return value

    def as_dict(self) -> Dict[str, Any]:
        return dict(self._data)

    def __repr__(self) -> str:
        return f"SCVPConfig({self._data!r})"


def load_config(
    path: Optional[str] = None,
    overrides: Optional[Dict[str, Any]] = None,
) -> SCVPConfig:
    """
    Build the effective SCVP configuration.

    Precedence (highest wins): overrides > environment variables >
    config file > built-in defaults.
    """
    data = json.loads(json.dumps(_DEFAULTS))  # cheap deep copy

    config_path = Path(path) if path else _find_config_file()
    if config_path:
        data = _deep_merge(data, _load_file(config_path))

    data = _deep_merge(data, _load_env_overrides())

    if overrides:
        data = _deep_merge(data, overrides)

    return SCVPConfig(data)
