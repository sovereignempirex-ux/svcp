import pytest

from scvp import Agent, AgentStatus, SCVPModel
from scvp.agents.planner import AgentPlanner
from scvp.agents.types import AgentContext, AgentTask
from scvp.core.exceptions import SCVPError
from scvp.tools import SCVPTool, ToolResult


class EchoTool(SCVPTool):
    name = "echo"

    def execute(self, arguments):
        return ToolResult(content=str(arguments["value"]))


class ToolPlanner(AgentPlanner):
    def plan(self, context):
        return [AgentTask("echo the value", tool_name="echo", arguments={"value": "ok"})]


class EmptyPlanner(AgentPlanner):
    def plan(self, context):
        return []


def test_agent_runs_model_goal():
    result = Agent(name="support", model=SCVPModel("mock")).run("hello")
    assert result.status == AgentStatus.COMPLETED
    assert "hello" in result.content
    assert result.state.step == 1


def test_agent_runs_injected_tool():
    agent = Agent(
        model=SCVPModel("mock"),
        tools={"echo": EchoTool()},
        planner=ToolPlanner(),
    )
    result = agent.run("use echo")
    assert result.content == "ok"
    assert result.state.tool_results[0].success is True


def test_agent_rejects_empty_goal():
    with pytest.raises(ValueError, match="must not be empty"):
        Agent().run(" ")


def test_agent_rejects_empty_plan():
    with pytest.raises(SCVPError, match="no tasks"):
        Agent(planner=EmptyPlanner()).run("anything")


def test_agent_records_failures():
    class BrokenTool(SCVPTool):
        name = "broken"

        def execute(self, arguments):
            raise RuntimeError("tool exploded")

    class BrokenPlanner(AgentPlanner):
        def plan(self, context):
            return [AgentTask("break", tool_name="broken")]

    agent = Agent(tools={"broken": BrokenTool()}, planner=BrokenPlanner())
    with pytest.raises(RuntimeError, match="tool exploded"):
        agent.run("break it")
    assert agent.runtime.last_context.state.status == AgentStatus.FAILED


def test_agent_honors_max_steps():
    class TwoStepPlanner(AgentPlanner):
        def plan(self, context):
            return [AgentTask("first"), AgentTask("second")]

    result = Agent(planner=TwoStepPlanner(), max_steps=1).run("do two things")
    assert result.status == AgentStatus.MAX_STEPS
    assert result.state.step == 1
