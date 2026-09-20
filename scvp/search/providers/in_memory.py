"""Deterministic in-process full-text search provider."""

from __future__ import annotations

import re
from copy import deepcopy
from threading import RLock
from typing import Dict, List

from scvp.search.base import SearchDocument, SearchProvider, SearchResult

_TOKEN_PATTERN = re.compile(r"\w+", re.UNICODE)


class InMemorySearchProvider(SearchProvider):
    """Search documents by case-insensitive token frequency."""

    def __init__(self):
        self._documents: Dict[str, SearchDocument] = {}
        self._lock = RLock()

    def index(self, document: SearchDocument) -> None:
        if not isinstance(document, SearchDocument):
            raise TypeError("document must be a SearchDocument instance.")
        if not document.id:
            raise ValueError("document.id must not be empty.")
        if not isinstance(document.content, str):
            raise TypeError("document.content must be a string.")
        with self._lock:
            self._documents[document.id] = deepcopy(document)

    def search(
        self,
        query: str,
        limit: int = 10,
        offset: int = 0,
    ) -> List[SearchResult]:
        if not isinstance(query, str) or not query.strip():
            return []
        if not isinstance(limit, int) or limit < 0:
            raise ValueError("limit must be zero or greater.")
        if not isinstance(offset, int) or offset < 0:
            raise ValueError("offset must be zero or greater.")

        query_tokens = self._tokens(query)
        with self._lock:
            matches = []
            for document in self._documents.values():
                document_tokens = self._tokens(document.content)
                score = sum(document_tokens.count(token) for token in query_tokens)
                if score:
                    matches.append(SearchResult(deepcopy(document), float(score)))

        matches.sort(key=lambda result: (-result.score, result.document.id))
        return matches[offset : offset + limit]

    def delete(self, document_id: str) -> None:
        with self._lock:
            self._documents.pop(document_id, None)

    def clear(self) -> None:
        with self._lock:
            self._documents.clear()

    @staticmethod
    def _tokens(value: str) -> List[str]:
        return [token.casefold() for token in _TOKEN_PATTERN.findall(value)]


InMemorySearch = InMemorySearchProvider