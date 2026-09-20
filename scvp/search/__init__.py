"""Provider-agnostic search contracts and built-in providers."""

from scvp.core.registry import Registry
from scvp.search.base import SearchDocument, SearchProvider, SearchResult
from scvp.search.providers.in_memory import InMemorySearch, InMemorySearchProvider
from scvp.search.providers.google import GoogleSearch, GoogleSearchProvider

search_registry = Registry("search")
search_registry.register("in_memory", InMemorySearchProvider)
search_registry.register("google", GoogleSearchProvider)

__all__ = [
    "SearchDocument",
    "SearchProvider",
    "SearchResult",
    "InMemorySearchProvider",
    "InMemorySearch",
    "GoogleSearchProvider",
    "GoogleSearch",
    "search_registry",
]