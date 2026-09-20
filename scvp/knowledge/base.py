"""Provider-agnostic knowledge base for retrieval-augmented generation."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from math import sqrt
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence

from scvp.search import SearchDocument, SearchProvider, SearchResult
from scvp.search.providers.in_memory import InMemorySearchProvider
from scvp.knowledge.chunking import TextChunker

Embedder = Callable[[List[str]], List[List[float]]]


@dataclass
class KnowledgeChunk:
    """A retrieved chunk and its source document identity."""

    document_id: str
    content: str
    score: float
    metadata: Dict[str, Any]


class KnowledgeBase:
    """Ingest documents, retrieve relevant chunks, and build RAG context."""

    def __init__(
        self,
        search: Optional[SearchProvider] = None,
        chunker: Optional[TextChunker] = None,
        embedder: Optional[Any] = None,
    ):
        self.search = search or InMemorySearchProvider()
        self.chunker = chunker or TextChunker()
        self.embedder = embedder
        self._document_chunks: Dict[str, List[str]] = {}
        self._vectors: Dict[str, List[float]] = {}
        self._chunk_documents: Dict[str, SearchDocument] = {}

    def ingest(
        self,
        document_id: str,
        content: str,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> int:
        """Replace a document and return the number of indexed chunks."""
        if not document_id:
            raise ValueError("document_id must not be empty.")
        if not isinstance(content, str):
            raise TypeError("content must be a string.")

        self.delete(document_id)
        chunks = self.chunker.split(content)
        chunk_ids = []
        base_metadata = dict(metadata or {})
        for index, chunk in enumerate(chunks):
            chunk_id = f"{document_id}::chunk-{index}"
            chunk_metadata = {
                **base_metadata,
                "source_document_id": document_id,
                "chunk_index": index,
            }
            self.search.index(SearchDocument(chunk_id, chunk, chunk_metadata))
            chunk_ids.append(chunk_id)
            self._chunk_documents[chunk_id] = SearchDocument(
                chunk_id, chunk, dict(chunk_metadata)
            )
        if self.embedder and chunks:
            for chunk_id, vector in zip(chunk_ids, self._embed(chunks)):
                self._vectors[chunk_id] = vector
        self._document_chunks[document_id] = chunk_ids
        return len(chunks)

    def retrieve(self, query: str, limit: int = 5) -> List[KnowledgeChunk]:
        """Retrieve relevant chunks while hiding search-provider details."""
        if limit < 0:
            raise ValueError("limit must be zero or greater.")
        if self.embedder:
            results = self._semantic_search(query, limit)
        else:
            results = self.search.search(query, limit=limit)
        return [self._to_chunk(result) for result in results]

    def build_context(self, query: str, limit: int = 5, separator: str = "\n\n") -> str:
        """Format retrieved chunks for inclusion in a model prompt."""
        chunks = self.retrieve(query, limit=limit)
        return separator.join(
            f"[Source: {chunk.document_id}]\n{chunk.content}" for chunk in chunks
        )

    def delete(self, document_id: str) -> None:
        """Remove all chunks belonging to a source document."""
        for chunk_id in self._document_chunks.pop(document_id, []):
            self.search.delete(chunk_id)
            self._vectors.pop(chunk_id, None)
            self._chunk_documents.pop(chunk_id, None)

    def clear(self) -> None:
        self.search.clear()
        self._document_chunks.clear()
        self._vectors.clear()
        self._chunk_documents.clear()

    def _semantic_search(self, query: str, limit: int) -> List[SearchResult]:
        query_vector = self._embed([query])[0]
        scored = []
        for chunk_id, vector in self._vectors.items():
            score = self._cosine_similarity(query_vector, vector)
            if score > 0:
                document = self._chunk_documents.get(chunk_id)
                if document:
                    scored.append(SearchResult(deepcopy(document), score))
        scored.sort(key=lambda result: (-result.score, result.document.id))
        return scored[:limit]

    def _embed(self, texts: List[str]) -> List[List[float]]:
        embed = self.embedder.embed if hasattr(self.embedder, "embed") else self.embedder
        vectors = embed(texts)
        if len(vectors) != len(texts):
            raise ValueError("embedder must return one vector per input text.")
        normalized = []
        for vector in vectors:
            if not isinstance(vector, Sequence) or not vector:
                raise ValueError("embedder returned an empty or invalid vector.")
            normalized.append([float(value) for value in vector])
        return normalized

    @staticmethod
    def _cosine_similarity(left: List[float], right: List[float]) -> float:
        if len(left) != len(right):
            raise ValueError("embedder returned vectors with inconsistent dimensions.")
        left_norm = sqrt(sum(value * value for value in left))
        right_norm = sqrt(sum(value * value for value in right))
        if not left_norm or not right_norm:
            return 0.0
        return sum(a * b for a, b in zip(left, right)) / (left_norm * right_norm)

    @staticmethod
    def _to_chunk(result: SearchResult) -> KnowledgeChunk:
        metadata = dict(result.document.metadata)
        document_id = metadata.pop("source_document_id", result.document.id)
        metadata.pop("chunk_index", None)
        return KnowledgeChunk(document_id, result.document.content, result.score, metadata)