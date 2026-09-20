"""
Mock Model Provider
=====================
A deterministic, dependency-free model provider used as SCVP's
default so the framework is runnable and testable out of the box,
without any API key or external service. This is the "Interface +
Mock Provider instead of an invented API" pattern for a capability
that would otherwise need a real external service.

Swap it out for a real provider once one is registered (OpenAI-
compatible, Anthropic-compatible, Ollama, ...) -- application code
written against `SCVPModel` does not change.
"""

from __future__ import annotations

import hashlib
from typing import Any, Iterable, List

from scvp.core.types import Message, ModelResponse, Role, StreamChunk, Usage
from scvp.models.base import ModelProvider, model_registry


class MockModelProvider(ModelProvider):
    name = "mock"

    def chat(self, messages: List[Message], **kwargs: Any) -> ModelResponse:
        last_user = next((m for m in reversed(messages) if m.role == Role.USER), None)
        prompt = last_user.content if last_user else ""
        content = f"[mock] you said: {prompt[:200]}"
        return ModelResponse(
            content=content,
            model="scvp-mock-1",
            provider=self.name,
            usage=Usage(
                prompt_tokens=len(prompt.split()),
                completion_tokens=len(content.split()),
                total_tokens=len(prompt.split()) + len(content.split()),
            ),
            finish_reason="stop",
            raw={"messages": [m.to_dict() for m in messages]},
        )

    def stream(self, messages: List[Message], **kwargs: Any) -> Iterable[StreamChunk]:
        response = self.chat(messages, **kwargs)
        words = response.content.split(" ")
        for i, word in enumerate(words):
            yield StreamChunk(delta=word + (" " if i < len(words) - 1 else ""))
        yield StreamChunk(delta="", done=True, finish_reason="stop")

    def embed(self, texts: List[str], **kwargs: Any) -> List[List[float]]:
        # Deterministic pseudo-embedding: hash each text into an 8-dim
        # vector. NOT semantically meaningful -- only useful for wiring
        # and testing the future memory & RAG pipelines before a real
        # embedding provider exists.
        vectors: List[List[float]] = []
        for text in texts:
            digest = hashlib.sha256(text.encode("utf-8")).digest()[:8]
            vectors.append([b / 255.0 for b in digest])
        return vectors

    def classify(self, text: str, labels: List[str], **kwargs: Any) -> str:
        if not labels:
            raise ValueError("classify() requires at least one label.")
        # Deterministic, content-blind heuristic: pick a label by hash so
        # results are stable across runs -- good enough to exercise the
        # interface end to end, not a real classifier.
        index = int(hashlib.sha256(text.encode("utf-8")).hexdigest(), 16) % len(labels)
        return labels[index]


model_registry.register("mock", MockModelProvider)
