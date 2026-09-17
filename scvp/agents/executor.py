"""Execution contracts for model and tool tasks."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Mapping

from scvp.agents.types import AgentContext, AgentTask
from scvp.core.types import Message, Role
from scvp.models.base import SCVPModel
from scvp.tools import SCVPTool, ToolResult


class AgentExecutor(ABC):
    """Executes one planned task."""

    @abstractmethod
    def execute(self, task: AgentTask, context: AgentContext) -> ToolResult:
        ...


class DefaultAgentExecutor(AgentExecutor):
    """Executes tool tasks or sends model tasks as user messages."""

    def __init__(self, model: SCVPModel, tools: Mapping[str, SCVPTool]):
        self.model = model
        self.tools = dict(tools)

    def execute(self, task: AgentTask, context: AgentContext) -> ToolResult:
        if task.tool_name:
            tool = self.tools.get(task.tool_name)
            if tool is None:
                raise KeyError("Unknown agent tool '{}'.".format(task.tool_name))
            tool.validate(task.arguments)
            return tool.execute(task.arguments)

        response = self.model.chat(
            list(context.state.messages)
            + [Message(role=Role.USER, content=task.description)]
        )
        return ToolResult(content=response.content, metadata={"model": response})
