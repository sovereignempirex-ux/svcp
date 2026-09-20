"""Plugin discovery and lifecycle manager."""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from importlib import metadata
from typing import Any, Dict, Iterable, Mapping, Optional

from scvp.plugins.types import Plugin, PluginContext, PluginInfo, PluginState


@dataclass
class _PluginRecord:
    plugin: Plugin
    context: PluginContext
    state: PluginState


class PluginManager:
    """Discover installed plugins and manage their lifecycle safely."""

    ENTRY_POINT_GROUP = "scvp.plugins"

    def __init__(self, config: Optional[Mapping[str, Any]] = None, services: Optional[Dict[str, Any]] = None):
        self.context = PluginContext(dict(config or {}), dict(services or {}))
        self._records: Dict[str, _PluginRecord] = {}

    def discover(self) -> Dict[str, PluginInfo]:
        """Return installed plugin metadata without importing plugin code."""
        return {
            entry_point.name: self._info_from_entry_point(entry_point)
            for entry_point in self._entry_points()
        }

    def load(self, name: str) -> Plugin:
        """Load one installed plugin and call its ``load`` hook."""
        if name in self._records:
            return self._records[name].plugin
        entry_point = next((item for item in self._entry_points() if item.name == name), None)
        if entry_point is None:
            raise KeyError(f"Plugin '{name}' is not installed.")
        plugin = self._coerce_plugin(entry_point.load())
        plugin.load(self.context)
        self._records[name] = _PluginRecord(plugin, self.context, PluginState.LOADED)
        return plugin

    def load_module(self, module_name: str, attribute: str = "plugin") -> Plugin:
        """Load a plugin object from an explicit module for development or tests."""
        module = importlib.import_module(module_name)
        plugin = self._coerce_plugin(getattr(module, attribute))
        name = plugin.info.name
        if name in self._records:
            return self._records[name].plugin
        plugin.load(self.context)
        self._records[name] = _PluginRecord(plugin, self.context, PluginState.LOADED)
        return plugin

    def enable(self, name: str) -> Plugin:
        record = self._record(name)
        if record.state == PluginState.ENABLED:
            return record.plugin
        record.plugin.enable(record.context)
        record.state = PluginState.ENABLED
        return record.plugin

    def disable(self, name: str) -> None:
        record = self._record(name)
        if record.state == PluginState.ENABLED:
            record.plugin.disable(record.context)
            record.state = PluginState.DISABLED

    def unload(self, name: str) -> None:
        record = self._record(name)
        if record.state == PluginState.ENABLED:
            self.disable(name)
        record.plugin.unload(record.context)
        del self._records[name]

    def enable_all(self, names: Optional[Iterable[str]] = None) -> None:
        selected = list(names) if names is not None else list(self.discover())
        for name in selected:
            self.enable(name) if name in self._records else self.enable_after_load(name)

    def enable_after_load(self, name: str) -> Plugin:
        self.load(name)
        return self.enable(name)

    def status(self) -> Dict[str, PluginState]:
        return {name: record.state for name, record in self._records.items()}

    def _record(self, name: str) -> _PluginRecord:
        if name not in self._records:
            raise KeyError(f"Plugin '{name}' is not loaded.")
        return self._records[name]

    @staticmethod
    def _coerce_plugin(value: Any) -> Plugin:
        plugin = value() if isinstance(value, type) else value
        if not isinstance(plugin, Plugin):
            raise TypeError("Plugin entry point must provide a Plugin instance or subclass.")
        return plugin

    @staticmethod
    def _info_from_entry_point(entry_point: Any) -> PluginInfo:
        distribution = getattr(entry_point, "dist", None)
        metadata_info = getattr(distribution, "metadata", {}) if distribution else {}
        return PluginInfo(
            name=entry_point.name,
            version=getattr(distribution, "version", "0.0.0"),
            description=metadata_info.get("Summary", ""),
        )

    @classmethod
    def _entry_points(cls):
        entries = metadata.entry_points()
        if hasattr(entries, "select"):
            return list(entries.select(group=cls.ENTRY_POINT_GROUP))
        return list(entries.get(cls.ENTRY_POINT_GROUP, []))