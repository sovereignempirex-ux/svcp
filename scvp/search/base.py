"""Provider-agnostic search contracts."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SearchDocument:
    """A searchable document with optional provider-specific metadata."""

    id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchResult:
    """A document returned by a search, ordered by descending score."""

    document: SearchDocument
    score: float


class SearchProvider(ABC):
    """Stores and searches documents behind a replaceable provider interface."""

    @abstractmethod
    def index(self, document: SearchDocument) -> None:
        """Insert or replace a document by id."""
        ...

    @abstractmethod
    def search(
        self,
        query: str,
        limit: int = 10,
        offset: int = 0,
    ) -> List[SearchResult]:
        """Return matching documents ordered by relevance."""
        ...

    @abstractmethod
    def delete(self, document_id: str) -> None:
        """Delete a document by id."""
        ...

    @abstractmethod
    def clear(self) -> None:
        """Delete all indexed documents."""
        ...