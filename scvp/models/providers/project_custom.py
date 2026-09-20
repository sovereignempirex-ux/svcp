"""
Project-specific custom model provider example.

This is a minimal provider implementation that follows the SCVP
`ModelProvider` contract and registers itself in the model registry.
It can be used as a base for a real project integration with an API,
local model, or custom business logic.
"""

from __future__ import annotations

from typing import Any, List

from scvp.core.types import Message, ModelResponse, Role
from scvp.models.base import ModelProvider, model_registry


class ProjectCustomModelProvider(ModelProvider):
    """Example provider for a project-specific AI backend."""

    name = "project_custom"

    def __init__(self, system_prompt: str = "You are a helpful project assistant.", model_name: str = "project-custom-1"):
        self.system_prompt = system_prompt
        self.model_name = model_name

    def chat(self, messages: List[Message], **kwargs: Any) -> ModelResponse:
        last_user = next((m for m in reversed(messages) if m.role == Role.USER), None)
        prompt = last_user.content.strip() if last_user else ""
        content = f"[{self.name}] {prompt or 'hello'}\n\n{self.system_prompt}"
        return ModelResponse(
            content=content,
            model=self.model_name,
            provider=self.name,
            raw={"messages": [m.to_dict() for m in messages], "system_prompt": self.system_prompt},
        )


model_registry.register("project_custom", ProjectCustomModelProvider, override=True)
