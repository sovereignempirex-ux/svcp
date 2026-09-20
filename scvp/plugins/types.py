"""Contracts shared by SCVP plugins."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Mapping, Optional


class PluginState(str, Enum):
    DISCOVERED = "discovered"
    LOADED = "loaded"
    ENABLED = "enabled"
    DISABLED = "disabled"
    FAILED = "failed"


@dataclass(frozen=True)
class PluginInfo:
    """Metadata used to identify and describe a plugin."""

    name: str
    version: str = "0.0.0"
    description: str = ""


@dataclass
class PluginContext:
    """Services and configuration exposed to a plugin during activation."""

    config: Mapping[str, Any] = field(default_factory=dict)
    services: Dict[str, Any] = field(default_factory=dict)


class Plugin:
    """Base lifecycle contract implemented by external plugins."""

    info = PluginInfo(name="unnamed")

    def load(self, context: PluginContext) -> None:
        """Prepare resources before activation."""

    def enable(self, context: PluginContext) -> None:
        """Register providers, routes, tools, or other capabilities."""

    def disable(self, context: PluginContext) -> None:
        """Stop plugin activity while keeping it loaded."""

    def unload(self, context: PluginContext) -> None:
        """Release resources owned by the plugin."""