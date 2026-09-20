import time

import pytest

from scvp import FunctionTool, ToolRegistry, ToolResult
from scvp.core.exceptions import (
    PermissionDeniedError,
    ProviderNotFoundError,
    SCVPTimeoutError,
    ValidationError,
)


def test_function_tool_returns_normalized_result():
    tool = FunctionTool("add", lambda args: args["left"] + args["right"])
    result = ToolRegistry([tool]).invoke("add", {"left": 2, "right": 3})
    assert result == ToolResult("5")


def test_schema_validation_rejects_missing_and_wrong_arguments():
    tool = FunctionTool(
        "lookup",
        lambda args: args["key"],
        schema={
            "type": "object",
            "required": ["key"],
            "properties": {"key": {"type": "string"}},
            "additionalProperties": False,
        },
    )
    registry = ToolRegistry([tool])
    with pytest.raises(ValidationError, match="Missing required"):
        registry.invoke("lookup", {})
    with pytest.raises(ValidationError, match="must be string"):
        registry.invoke("lookup", {"key": 3})


def test_registry_enforces_permissions_and_reports_missing_tools():
    registry = ToolRegistry(
        [FunctionTool("secret", lambda args: "ok", permissions=("private",))]
    )
    with pytest.raises(PermissionDeniedError):
        registry.invoke("secret")
    with pytest.raises(ProviderNotFoundError):
        registry.invoke("missing")
    assert registry.list() == ["secret"]


def test_registry_enforces_tool_timeout():
    def slow_tool(arguments):
        time.sleep(0.05)
        return "done"

    registry = ToolRegistry([FunctionTool("slow", slow_tool, timeout=0.001)])
    with pytest.raises(SCVPTimeoutError):
        registry.invoke("slow")