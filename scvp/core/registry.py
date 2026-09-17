"""
SCVP Provider Registry
=========================
A small generic registry used everywhere SCVP needs a swappable
provider: model providers today; tool providers, search providers,
memory backends, etc. in later phases. This is what keeps SCVP Core
free of any hard dependency on a specific vendor or backend -- Core
only ever talks to a `Registry`, never to `OpenAIProvider` or
`RedisMemory` directly.
"""

from __future__ import annotations

from typing import Callable, Dict, Generic, List, Optional, TypeVar

from scvp.core.exceptions import ProviderAlreadyRegisteredError, ProviderNotFoundError

T = TypeVar("T")


class Registry(Generic[T]):
    """A named registry of factories for a single provider kind (e.g. 'model')."""

    def __init__(self, kind: str):
        self.kind = kind
        self._factories: Dict[str, Callable[..., T]] = {}
        self._instances: Dict[str, T] = {}

    def register(
        self,
        name: str,
        factory: Optional[Callable[..., T]] = None,
        override: bool = False,
    ):
        """
        Register a factory under `name`. Usable as a direct call:

            registry.register("mock", MockModelProvider)

        or as a decorator:

            @registry.register("mock")
            class MockModelProvider(ModelProvider): ...
        """
        if factory is None:
            def decorator(fn_or_cls: Callable[..., T]) -> Callable[..., T]:
                self._do_register(name, fn_or_cls, override)
                return fn_or_cls
            return decorator

        self._do_register(name, factory, override)
        return factory

    def _do_register(self, name: str, factory: Callable[..., T], override: bool) -> None:
        if name in self._factories and not override:
            raise ProviderAlreadyRegisteredError(
                f"{self.kind} provider '{name}' is already registered. "
                f"Pass override=True to replace it."
            )
        self._factories[name] = factory

    def get(self, name: str, *args, **kwargs) -> T:
        """Instantiate (and cache) the provider registered under `name`."""
        if name not in self._factories:
            raise ProviderNotFoundError(self.kind, name, list(self._factories))
        if name not in self._instances:
            self._instances[name] = self._factories[name](*args, **kwargs)
        return self._instances[name]

    def list(self) -> List[str]:
        return sorted(self._factories)

    def is_registered(self, name: str) -> bool:
        return name in self._factories

    def unregister(self, name: str) -> None:
        self._factories.pop(name, None)
        self._instances.pop(name, None)
