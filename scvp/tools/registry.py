"""Registration and safe invocation of agent tools."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from typing import Any, Dict, Iterable, Mapping, Optional

from scvp.core.exceptions import (
    PermissionDeniedError,
    ProviderAlreadyRegisteredError,
    ProviderNotFoundError,
    SCVPTimeoutError,
    ValidationError,
)
from scvp.tools.base import SCVPTool, ToolResult


class ToolRegistry:
    """Named collection of tools with validation and invocation controls."""

    def __init__(self, tools: Optional[Iterable[SCVPTool]] = None):
        self._tools: Dict[str, SCVPTool] = {}
        for tool in tools or ():
            self.register(tool)

    def register(self, tool: SCVPTool, override: bool = False) -> SCVPTool:
        if not isinstance(tool, SCVPTool):
            raise TypeError("tool must be an SCVPTool instance")
        if not tool.name or not tool.name.strip():
            raise ValidationError("Tool name must not be empty.")
        if tool.name in self._tools and not override:
            raise ProviderAlreadyRegisteredError(
                "tool '{}' is already registered. Pass override=True to replace it.".format(
                    tool.name
                )
            )
        self._tools[tool.name] = tool
        return tool

    def get(self, name: str) -> SCVPTool:
        try:
            return self._tools[name]
        except KeyError:
            raise ProviderNotFoundError("tool", name, self.list())

    def list(self):
        return sorted(self._tools)

    def is_registered(self, name: str) -> bool:
        return name in self._tools

    def unregister(self, name: str) -> None:
        self._tools.pop(name, None)

    def invoke(
        self,
        name: str,
        arguments: Optional[Mapping[str, Any]] = None,
        granted_permissions: Iterable[str] = (),
    ) -> ToolResult:
        tool = self.get(name)
        missing_permissions = set(tool.permissions) - set(granted_permissions)
        if missing_permissions:
            raise PermissionDeniedError(
                "Tool '{}' requires permission(s): {}.".format(
                    name, ", ".join(sorted(missing_permissions))
                )
            )
        call_arguments = dict(arguments or {})
        tool.validate(call_arguments)
        try:
            if tool.timeout is None:
                result = tool.execute(call_arguments)
            else:
                if tool.timeout <= 0:
                    raise ValueError("tool timeout must be positive")
                pool = ThreadPoolExecutor(max_workers=1)
                future = pool.submit(tool.execute, call_arguments)
                try:
                    result = future.result(timeout=tool.timeout)
                finally:
                    pool.shutdown(wait=False, cancel_futures=True)
        except FutureTimeoutError as exc:
            raise SCVPTimeoutError(
                "Tool '{}' exceeded timeout ({}s).".format(name, tool.timeout)
            ) from exc
        if not isinstance(result, ToolResult):
            raise ValidationError(
                "Tool '{}' must return a ToolResult.".format(name)
            )
        return result


tool_registry = ToolRegistry()
