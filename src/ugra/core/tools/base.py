"""Universal tool system — tools plug in without modifying agent code."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any
from uuid import UUID


class ToolName(StrEnum):
    JOB_SEARCH = "job_search"
    RESUME = "resume"
    COVER_LETTER = "cover_letter"
    INTERVIEW = "interview"
    LEARNING = "learning"
    NOTIFICATION = "notification"


@dataclass
class ToolContext:
    user_id: UUID
    agent_name: str
    parameters: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolResult:
    tool_name: str
    success: bool
    data: dict[str, Any] = field(default_factory=dict)
    message: str = ""
    reasoning: str = ""


class AgentTool(ABC):
    """Base class for all agent tools."""

    @property
    @abstractmethod
    def name(self) -> ToolName: ...

    @property
    def description(self) -> str:
        return f"Tool: {self.name.value}"

    @abstractmethod
    async def execute(self, context: ToolContext) -> ToolResult: ...

    async def can_execute(self, context: ToolContext) -> bool:
        return True


# Canonical interface name from AI Core spec
IAgentTool = AgentTool


class ToolRegistry:
    """Auto-discovery registry for agent tools."""

    def __init__(self) -> None:
        self._tools: dict[ToolName, AgentTool] = {}

    def register(self, tool: AgentTool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: ToolName) -> AgentTool | None:
        return self._tools.get(name)

    @property
    def tools(self) -> list[AgentTool]:
        return list(self._tools.values())

    def names(self) -> list[str]:
        return [t.name.value for t in self._tools.values()]

    async def execute(self, name: ToolName, context: ToolContext) -> ToolResult:
        tool = self._tools.get(name)
        if not tool:
            return ToolResult(tool_name=name.value, success=False, message=f"Tool '{name}' not found")
        if not await tool.can_execute(context):
            return ToolResult(tool_name=name.value, success=False, message="Tool cannot execute in this context")
        return await tool.execute(context)
