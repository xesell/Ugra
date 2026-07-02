"""Agent plugin system — extensible without modifying existing code."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any
from uuid import UUID

from langgraph.graph.state import CompiledStateGraph


class AgentCapability(StrEnum):
    JOB_SEARCH = "job_search"
    JOB_ANALYSIS = "job_analysis"
    RESUME = "resume"
    COVER_LETTER = "cover_letter"
    SKILL_GAP = "skill_gap"
    LEARNING = "learning"
    INTERVIEW = "interview"
    SALARY = "salary"
    HR = "hr"


@dataclass
class AgentContext:
    user_id: UUID
    message: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResponse:
    agent_name: str
    content: str
    data: dict[str, Any] = field(default_factory=dict)
    capabilities_used: list[AgentCapability] = field(default_factory=list)


class BaseAgent(ABC):
    """Base class for all Ugra agents. Each agent is a self-contained module."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def capabilities(self) -> list[AgentCapability]: ...

    @abstractmethod
    async def can_handle(self, context: AgentContext) -> float:
        """Return confidence score 0-1 for handling this request."""

    @abstractmethod
    async def invoke(self, context: AgentContext) -> AgentResponse: ...

    @property
    def graph(self) -> CompiledStateGraph | None:
        return None


class AgentRegistry:
    """Plugin registry for agents. New agents register here without code changes."""

    def __init__(self) -> None:
        self._agents: dict[str, BaseAgent] = {}

    def register(self, agent: BaseAgent) -> None:
        self._agents[agent.name] = agent

    def get(self, name: str) -> BaseAgent | None:
        return self._agents.get(name)

    @property
    def agents(self) -> list[BaseAgent]:
        return list(self._agents.values())

    def by_capability(self, capability: AgentCapability) -> list[BaseAgent]:
        return [a for a in self._agents.values() if capability in a.capabilities]
