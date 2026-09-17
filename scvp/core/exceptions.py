"""
SCVP Core Exceptions
=====================
Central exception hierarchy for the whole SCVP framework.

Every error raised anywhere in SCVP (core, models, agents, tools,
search, memory, plugins, api, cli) should subclass SCVPError so that
callers can catch `SCVPError` and handle any framework failure
uniformly, while still being able to catch a specific subtype when
they need finer-grained handling.
"""

from __future__ import annotations

from typing import List, Optional


class SCVPError(Exception):
    """Base class for all SCVP errors."""


class ConfigError(SCVPError):
    """Raised when configuration is missing, malformed, or invalid."""


class RegistryError(SCVPError):
    """Base class for provider/plugin registry errors."""


class ProviderNotFoundError(RegistryError):
    """Raised when a requested provider name is not registered."""

    def __init__(self, kind: str, name: str, available: Optional[List[str]] = None):
        available = available or []
        msg = f"No {kind} provider named '{name}' is registered."
        if available:
            msg += f" Available: {', '.join(sorted(available))}"
        else:
            msg += " No providers of this kind are registered yet."
        super().__init__(msg)
        self.kind = kind
        self.name = name
        self.available = available


class ProviderAlreadyRegisteredError(RegistryError):
    """Raised when a provider name is registered twice without override=True."""


class ModelError(SCVPError):
    """Raised for model-provider level failures (generation, embedding, etc.)."""


class ModelCapabilityNotSupportedError(ModelError):
    """Raised when a provider does not implement a given SCVPModel capability."""

    def __init__(self, provider_name: str, capability: str):
        super().__init__(
            f"Provider '{provider_name}' does not support '{capability}()'."
        )
        self.provider_name = provider_name
        self.capability = capability


class ValidationError(SCVPError):
    """Raised when input/output validation fails."""


class PermissionDeniedError(SCVPError):
    """Raised when an operation is attempted without the required permission."""


class SCVPTimeoutError(SCVPError):
    """Raised when an operation exceeds its allotted time budget."""
