"""Adapters for real semantic embeddings."""

from __future__ import annotations

from typing import List, Optional


class SentenceTransformerEmbedder:
    """Lazy adapter around a sentence-transformers embedding model."""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None

    def embed(self, texts: List[str]) -> List[List[float]]:
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:
                raise RuntimeError(
                    "Install SCVP embeddings support with: "
                    "pip install 'scvp[embeddings]'"
                ) from exc
            self._model = SentenceTransformer(self.model_name)
        vectors = self._model.encode(texts, convert_to_numpy=True)
        return [vector.tolist() for vector in vectors]