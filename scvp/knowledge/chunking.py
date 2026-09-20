"""Deterministic text chunking for knowledge ingestion."""

from __future__ import annotations

from typing import List


class TextChunker:
    """Split text into bounded character chunks with optional overlap."""

    def __init__(self, chunk_size: int = 1000, overlap: int = 100):
        if chunk_size < 1:
            raise ValueError("chunk_size must be greater than zero.")
        if overlap < 0 or overlap >= chunk_size:
            raise ValueError("overlap must be non-negative and smaller than chunk_size.")
        self.chunk_size = chunk_size
        self.overlap = overlap

    def split(self, text: str) -> List[str]:
        if not isinstance(text, str):
            raise TypeError("text must be a string.")
        if not text:
            return []

        chunks = []
        start = 0
        step = self.chunk_size - self.overlap
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end == len(text):
                break
            start += step
        return chunks