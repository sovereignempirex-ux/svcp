"""
SCVP Model Layer — Provider Interface
========================================
`ModelProvider` is the contract every model backend must implement
(SCVP native, OpenAI-compatible, Anthropic-compatible, local models
via Ollama/llama.cpp, etc.). `SCVPModel` is the stable, public-facing
class application code is written against; it never changes when the
underlying provider is swapped.

No provider is assumed to exist by default except the built-in
`MockModelProvider` (see `scvp.models.providers.mock`), which exists
purely so SCVP is runnable and testable with zero external
dependencies or API keys. Real provider adapters (OpenAI-compatible,
Anthropic-compatible, Ollama, ...) are future work and register into
`model_registry` the exact same way `MockModelProvider` does.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Iterable, List

from scvp.core.exceptions import ModelCapabilityNotSupportedError
from scvp.core.registry import Registry
from scvp.core.types import Message, ModelResponse, Role, StreamChunk

model_registry: "Registry[ModelProvider]" = Registry(kind="model")


class ModelProvider(ABC):
    """
    Base class every model backend adapter must subclass.

    Only `chat` is strictly required. Providers that can't support a
    capability simply don't override it -- the default raises
    `ModelCapabilityNotSupportedError` so callers get a clear error
    instead of a silent no-op or a wrong answer.
    """

    name: str = "base"

    @abstractmethod
    def chat(self, messages: List[Message], **kwargs: Any) -> ModelResponse:
        ...

    def generate(self, prompt: str, **kwargs: Any) -> ModelResponse:
        """Default: treat a single prompt as a one-message chat turn."""
        return self.chat([Message(role=Role.USER, content=prompt)], **kwargs)

    def stream(self, messages: List[Message], **kwargs: Any) -> Iterable[StreamChunk]:
        raise ModelCapabilityNotSupportedError(self.name, "stream")

    def embed(self, texts: List[str], **kwargs: Any) -> List[List[float]]:
        raise ModelCapabilityNotSupportedError(self.name, "embed")

    def classify(self, text: str, labels: List[str], **kwargs: Any) -> str:
        raise ModelCapabilityNotSupportedError(self.name, "classify")

    def reason(self, messages: List[Message], **kwargs: Any) -> ModelResponse:
        """
        Default: same as chat(). Providers with a dedicated
        reasoning/thinking mode override this.
        """
        return self.chat(messages, **kwargs)


class SCVPModel:
    """
    The stable, provider-agnostic class application code is written
    against. Swapping the underlying provider never requires changing
    code that uses SCVPModel.

        model = SCVPModel(provider="mock")
        response = model.chat([Message(role=Role.USER, content="hi")])
    """

    def __init__(self, provider: str = "mock", **provider_kwargs: Any):
        self._provider_name = provider
        self._provider: ModelProvider = model_registry.get(provider, **provider_kwargs)

    @classmethod
    def from_config(cls, config: Any) -> "SCVPModel":
        """Build a model from either the new ``models`` or legacy ``model`` schema."""
        provider = config.get("models.default") or config.get("model.provider", "mock")
        kwargs = dict(config.get(f"models.providers.{provider}", {}) or {})
        if not isinstance(kwargs, dict):
            raise TypeError(f"Configuration for model provider '{provider}' must be a mapping.")
        kwargs.pop("type", None)
        return cls(provider=provider, **kwargs)

    @property
    def provider_name(self) -> str:
        return self._provider_name

    def generate(self, prompt: str, **kwargs: Any) -> ModelResponse:
        return self._provider.generate(prompt, **kwargs)

    def chat(self, messages: List[Message], **kwargs: Any) -> ModelResponse:
        return self._provider.chat(messages, **kwargs)

    def stream(self, messages: List[Message], **kwargs: Any) -> Iterable[StreamChunk]:
        return self._provider.stream(messages, **kwargs)

    def embed(self, texts: List[str], **kwargs: Any) -> List[List[float]]:
        return self._provider.embed(texts, **kwargs)

    def classify(self, text: str, labels: List[str], **kwargs: Any) -> str:
        return self._provider.classify(text, labels, **kwargs)

    def reason(self, messages: List[Message], **kwargs: Any) -> ModelResponse:
        return self._provider.reason(messages, **kwargs)
