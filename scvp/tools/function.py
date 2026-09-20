"""Adapters for exposing ordinary Python callables as SCVP tools."""

from __future__ import annotations

from typing import Any, Callable, Mapping, Optional

from scvp.tools.base import SCVPTool, ToolResult


class FunctionTool(SCVPTool):
    """Turn a callable accepting one mapping into an ``SCVPTool``."""

    def __init__(
        self,
        name: str,
        function: Callable[[Mapping[str, Any]], Any],
        description: str = "",
        schema: Optional[Mapping[str, Any]] = None,
        permissions=(),
        timeout: Optional[float] = None,
    ):
        self.name = name
        self.function = function
        self.description = description
        self.schema = schema or {}
        self.permissions = tuple(permissions)
        self.timeout = timeout

    def execute(self, arguments: Mapping[str, Any]) -> ToolResult:
        result = self.function(arguments)
        return result if isinstance(result, ToolResult) else ToolResult(str(result))
