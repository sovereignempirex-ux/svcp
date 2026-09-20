"""Provider-agnostic tool contracts for the Agent Runtime."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional

from scvp.core.exceptions import ValidationError


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

        Concrete tools can override this method for domain-specific checks.
        The default implementation supports the common JSON-schema fields
        used by agent tool calls.
        """
        if not isinstance(arguments, Mapping):
            raise ValidationError("Tool arguments must be a mapping.")

        required = self.schema.get("required", [])
        missing = [name for name in required if name not in arguments]
        if missing:
            raise ValidationError(
                "Missing required tool arguments: {}.".format(
                    ", ".join(sorted(missing))
                )
            )

        properties = self.schema.get("properties", {})
        if self.schema.get("additionalProperties", True) is False:
            unknown = sorted(set(arguments) - set(properties))
            if unknown:
                raise ValidationError(
                    "Unknown tool arguments: {}.".format(", ".join(unknown))
                )

        for name, value in arguments.items():
            expected = properties.get(name, {}).get("type")
            if expected is None:
                continue
            expected_types = {
                "string": str,
                "number": (int, float),
                "integer": int,
                "boolean": bool,
                "object": Mapping,
                "array": (list, tuple),
            }
            python_type = expected_types.get(expected)
            if python_type is not None and (
                not isinstance(value, python_type)
                or expected in ("number", "integer") and isinstance(value, bool)
            ):
                raise ValidationError(
                    "Tool argument '{}' must be {}.".format(name, expected)
                )

    @abstractmethod
    def execute(self, arguments: Mapping[str, Any]) -> ToolResult:
        """Execute the tool with already validated arguments."""

