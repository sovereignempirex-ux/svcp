from scvp import Plugin, PluginInfo, PluginManager, PluginState


class ExamplePlugin(Plugin):
    info = PluginInfo("example", "1.0.0", "Test plugin")

    def __init__(self):
        self.events = []

    def load(self, context):
        self.events.append(("load", context.services["value"]))

    def enable(self, context):
        self.events.append("enable")

    def disable(self, context):
        self.events.append("disable")

    def unload(self, context):
        self.events.append("unload")


def test_module_plugin_lifecycle():
    manager = PluginManager(services={"value": 42})
    manager.load_module("tests.test_plugins", "example_plugin")
    manager.enable("example")
    assert manager.status() == {"example": PluginState.ENABLED}
    manager.disable("example")
    manager.unload("example")


example_plugin = ExamplePlugin()


def test_plugin_metadata_and_missing_plugin():
    manager = PluginManager(services={"value": 42})
    assert manager.load_module("tests.test_plugins", "example_plugin").info.name == "example"
    assert manager.status()["example"] == PluginState.LOADED