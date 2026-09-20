"""Core data contracts for SCVP agents."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from scvp.core.types import Message
from scvp.tools import ToolResult


class AgentStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    MAX_STEPS = "max_steps"


@dataclass
class AgentTask:
    """One planned unit of work."""

    description: str
    tool_name: Optional[str] = None
    arguments: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentState:
    """Mutable execution state exposed to observers and callers."""

    status: AgentStatus = AgentStatus.IDLE
    step: int = 0
    messages: List[Message] = field(default_factory=list)
    tool_results: List[ToolResult] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class AgentContext:
    """Short-term context shared by planner and executor."""

    goal: str
    state: AgentState = field(default_factory=AgentState)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_message(self, message: Message) -> None:
        self.state.messages.append(message)


@dataclass
class AgentResult:
    """Stable result returned by ``Agent.run``."""

    content: str
    status: AgentStatus
    state: AgentState

