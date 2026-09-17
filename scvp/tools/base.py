"""Provider-agnostic tool contracts for the Agent Runtime."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional


@dataclass
class ToolResult:
    """Normalized result returned by every tool invocation."""

    content: str
    success: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


class SCVPTool(ABC):
    """Base contract for tools that an agent may explicitly invoke."""

    name: str = "tool"
    description: str = ""
    schema: Mapping[str, Any] = {}
    permissions: tuple = ()
    timeout: Optional[float] = None

    def validate(self, arguments: Mapping[str, Any]) -> None:
        """Validate arguments before execution.

        Concrete tools can override this method to enforce their schema.
        """

    @abstractmethod
    def execute(self, arguments: Mapping[str, Any]) -> ToolResult:
        """Execute the tool with already validated arguments."""

