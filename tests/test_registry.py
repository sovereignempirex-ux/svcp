import pytest

from scvp.core.exceptions import ProviderAlreadyRegisteredError, ProviderNotFoundError
from scvp.core.registry import Registry


def test_register_and_get():
    registry = Registry(kind="widget")
    registry.register("a", lambda: "instance-a")
    assert registry.get("a") == "instance-a"


def test_decorator_style():
    registry = Registry(kind="widget")

    @registry.register("b")
    class Thing:
        def __init__(self):
            self.value = "b"

    assert registry.get("b").value == "b"


def test_missing_provider_raises():
    registry = Registry(kind="widget")
    with pytest.raises(ProviderNotFoundError):
        registry.get("nope")


def test_duplicate_registration_raises():
    registry = Registry(kind="widget")
    registry.register("a", lambda: "x")
    with pytest.raises(ProviderAlreadyRegisteredError):
        registry.register("a", lambda: "y")


def test_override_allows_replacement():
    registry = Registry(kind="widget")
    registry.register("a", lambda: "x")
    registry.register("a", lambda: "y", override=True)
    assert registry.get("a") == "y"


def test_instances_are_cached():
    registry = Registry(kind="widget")
    calls = []
    registry.register("a", lambda: calls.append(1) or object())
    first = registry.get("a")
    second = registry.get("a")
    assert first is second
    assert len(calls) == 1


def test_list_and_is_registered():
    registry = Registry(kind="widget")
    registry.register("b", lambda: "b")
    registry.register("a", lambda: "a")
    assert registry.list() == ["a", "b"]
    assert registry.is_registered("a") is True
    assert registry.is_registered("z") is False
