"""Sequential Agent Runtime MVP."""

from __future__ import annotations

from typing import Mapping, Optional

from scvp.core.types import Message, Role
from scvp.models.base import SCVPModel
from scvp.agents.executor import AgentExecutor, DefaultAgentExecutor
from scvp.agents.planner import AgentPlanner, SingleStepPlanner
from scvp.agents.types import AgentContext, AgentResult, AgentStatus
from scvp.core.exceptions import SCVPError
from scvp.tools import SCVPTool


class AgentRuntime:
    """Coordinates planning and execution with an explicit step budget."""

    def __init__(
        self,
        model: Optional[SCVPModel] = None,
        tools: Optional[Mapping[str, SCVPTool]] = None,
        planner: Optional[AgentPlanner] = None,
        executor: Optional[AgentExecutor] = None,
        max_steps: int = 8,
    ):
        if max_steps < 1:
            raise ValueError("max_steps must be at least 1.")
        self.model = model or SCVPModel()
        self.tools = dict(tools or {})
        self.planner = planner or SingleStepPlanner()
        self.executor = executor or DefaultAgentExecutor(self.model, self.tools)
        self.max_steps = max_steps
        self.last_context: Optional[AgentContext] = None

    def run(self, goal: str, metadata: Optional[Mapping[str, object]] = None) -> AgentResult:
        if not goal or not goal.strip():
            raise ValueError("Agent goal must not be empty.")

        context = AgentContext(goal=goal, metadata=dict(metadata or {}))
        self.last_context = context
        context.state.status = AgentStatus.RUNNING
        try:
            tasks = self.planner.plan(context)
            if not tasks:
                raise SCVPError("Agent planner returned no tasks.")

            final_content = ""
            for task in tasks:
                if context.state.step >= self.max_steps:
                    context.state.status = AgentStatus.MAX_STEPS
                    return AgentResult(final_content, context.state.status, context.state)
                context.state.step += 1
                result = self.executor.execute(task, context)
                context.state.tool_results.append(result)
                context.add_message(Message(role=Role.TOOL, content=result.content))
                final_content = result.content
                if not result.success:
                    raise SCVPError(
                        "Agent task '{}' failed.".format(task.description)
                    )

            context.state.status = AgentStatus.COMPLETED
            return AgentResult(final_content, context.state.status, context.state)
        except Exception as exc:
            context.state.status = AgentStatus.FAILED
            context.state.error = str(exc)
            raise


class Agent:
    """Public convenience API for running one agent."""

    def __init__(
        self,
        name: str = "agent",
        model: Optional[SCVPModel] = None,
        tools: Optional[Mapping[str, SCVPTool]] = None,
        planner: Optional[AgentPlanner] = None,
        max_steps: int = 8,
    ):
        self.name = name
        self.runtime = AgentRuntime(
            model=model, tools=tools, planner=planner, max_steps=max_steps
        )

    def run(self, goal: str, metadata: Optional[Mapping[str, object]] = None) -> AgentResult:
        return self.runtime.run(goal, metadata=metadata)
