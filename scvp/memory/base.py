"""Provider-agnostic memory contracts."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from scvp.core.types import Message


class MemoryProvider(ABC):
    """Stores conversation messages behind a replaceable provider interface."""

    @abstractmethod
    def save(self, conversation_id: str, message: Message) -> None:
        """Append a message to a conversation."""
        ...

    @abstractmethod
    def load(self, conversation_id: str, limit: Optional[int] = None) -> List[Message]:
        """Return conversation messages in insertion order."""
        ...

    @abstractmethod
    def delete(self, conversation_id: str) -> None:
        """Delete all messages for a conversation."""
        ...

    @abstractmethod
    def clear(self) -> None:
        """Delete all conversations."""
        ...