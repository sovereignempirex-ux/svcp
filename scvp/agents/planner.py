"""Planning contracts and the default single-step planner."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from scvp.agents.types import AgentContext, AgentTask


class AgentPlanner(ABC):
    """Converts an agent context into executable tasks."""

    @abstractmethod
    def plan(self, context: AgentContext) -> List[AgentTask]:
        ...


class SingleStepPlanner(AgentPlanner):
    """Default planner: ask the model to answer the goal in one step."""

    def plan(self, context: AgentContext) -> List[AgentTask]:
        return [AgentTask(description=context.goal)]

