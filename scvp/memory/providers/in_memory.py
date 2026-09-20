"""Deterministic in-process memory provider."""

from __future__ import annotations

from copy import deepcopy
from threading import RLock
from typing import Dict, List, Optional

from scvp.core.types import Message
from scvp.memory.base import MemoryProvider


class InMemoryProvider(MemoryProvider):
    """Keep conversation messages in process memory without external services."""

    def __init__(self):
        self._conversations: Dict[str, List[Message]] = {}
        self._lock = RLock()

    def save(self, conversation_id: str, message: Message) -> None:
        if not conversation_id:
            raise ValueError("conversation_id must not be empty.")
        if not isinstance(message, Message):
            raise TypeError("message must be a Message instance.")
        with self._lock:
            self._conversations.setdefault(conversation_id, []).append(deepcopy(message))

    def load(self, conversation_id: str, limit: Optional[int] = None) -> List[Message]:
        if limit is not None and limit < 0:
            raise ValueError("limit must be zero or greater.")
        with self._lock:
            messages = self._conversations.get(conversation_id, [])
            selected = messages if limit is None else messages[-limit:] if limit else []
            return deepcopy(selected)

    def delete(self, conversation_id: str) -> None:
        with self._lock:
            self._conversations.pop(conversation_id, None)

    def clear(self) -> None:
        with self._lock:
            self._conversations.clear()


InMemoryMemory = InMemoryProvider