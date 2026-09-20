"""
SCVP Core Types
================
Shared data types used across every layer of SCVP (models, agents,
tools, memory, api). Kept dependency-free and provider-agnostic on
purpose: nothing in here should import from `scvp.models`,
`scvp.agents`, etc. Other layers import from here, never the reverse.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class Role(str, Enum):
    """Who a message in a conversation came from."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class Message:
    """A single turn in a conversation, passed to/returned from a model."""

    role: Role
    content: str
    name: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"role": self.role.value, "content": self.content}
        if self.name:
            d["name"] = self.name
        if self.metadata:
            d["metadata"] = self.metadata
        return d


@dataclass
class Usage:
    """Token/cost accounting for a single model call."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass
class ModelResponse:
    """Normalized response returned by every model provider, regardless of vendor."""

    content: str
    model: str
    provider: str
    usage: Usage = field(default_factory=Usage)
    finish_reason: Optional[str] = None
    raw: Any = None
    request_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    created_at: float = field(default_factory=time.time)


@dataclass
class StreamChunk:
    """A single chunk yielded by a provider's stream() call."""

    delta: str
    done: bool = False
    finish_reason: Optional[str] = None
    raw: Any = None
