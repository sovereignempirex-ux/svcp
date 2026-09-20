"""Local project model provider.

This provider is designed for a project-specific local AI backend. It does not
require any external API or network access. The implementation is intentionally
simple and deterministic so it matches the SCVP provider abstraction while
remaining easy to replace with a real local model adapter later.
"""

from __future__ import annotations

import re
from typing import Any, Iterable, List

from scvp.core.types import Message, ModelResponse, Role, StreamChunk
from scvp.models.base import ModelProvider, model_registry


class LocalProjectModelProvider(ModelProvider):
    """A local, project-specific model backend."""

    name = "local_project"

    def __init__(
        self,
        model_name: str = "local-project-v1",
        system_prompt: str = "أنت مساعد محلي داخل المشروع. أجب باختصار ووضوح.",
        max_chars: int = 500,
    ):
        self.model_name = model_name
        self.system_prompt = system_prompt
        self.max_chars = max_chars

    def _normalize_text(self, text: str) -> str:
        text = re.sub(r"\s+", " ", text).strip()
        return text[: self.max_chars]

    def chat(self, messages: List[Message], **kwargs: Any) -> ModelResponse:
        last_user = next((m for m in reversed(messages) if m.role == Role.USER), None)
        prompt = last_user.content if last_user else ""
        prompt_norm = self._normalize_text(prompt)

        if not prompt_norm:
            content = self.system_prompt
        else:
            content = (
                f"[local-project] تم استلام الطلب: {prompt_norm}\n\n"
                f"{self.system_prompt}"
            )

        return ModelResponse(
            content=content,
            model=self.model_name,
            provider=self.name,
            raw={
                "messages": [m.to_dict() for m in messages],
                "system_prompt": self.system_prompt,
            },
        )

    def stream(self, messages: List[Message], **kwargs: Any) -> Iterable[StreamChunk]:
        """Yield the local response in word-sized chunks."""
        response = self.chat(messages, **kwargs)
        words = response.content.split(" ")
        for index, word in enumerate(words):
            yield StreamChunk(delta=word + (" " if index < len(words) - 1 else ""))
        yield StreamChunk(delta="", done=True, finish_reason="stop")


model_registry.register("local_project", LocalProjectModelProvider, override=True)
