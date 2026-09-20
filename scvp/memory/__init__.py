from scvp.core.registry import Registry
from scvp.memory.base import MemoryProvider
from scvp.memory.providers.in_memory import InMemoryMemory, InMemoryProvider

memory_registry = Registry("memory")
memory_registry.register("in_memory", InMemoryProvider)

__all__ = [
    "MemoryProvider",
    "InMemoryProvider",
    "InMemoryMemory",
    "memory_registry",
]