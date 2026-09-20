"""Standalone local model provider backed by Transformers or GGUF."""

from scvp.models.base import model_registry
from scvp.models.providers.custom import CustomModelProvider


class LocalModelProvider(CustomModelProvider):
    """Run a real model from a local directory or `.gguf` file."""

    name = "local"


model_registry.register("local", LocalModelProvider, override=True)