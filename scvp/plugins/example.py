"""Small built-in plugin showing the external plugin contract."""

from scvp.plugins.types import Plugin, PluginInfo


class ExamplePlugin(Plugin):
    info = PluginInfo("example", "0.1.0", "SCVP lifecycle example plugin")


plugin = ExamplePlugin()