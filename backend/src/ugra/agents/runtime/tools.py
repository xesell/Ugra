"""AgentTools — facade over tool registry for agents."""

from uuid import UUID

from ugra.core.tools.base import AgentTool, IAgentTool, ToolContext, ToolName, ToolRegistry, ToolResult


class AgentTools:
    """Agent-facing tool API."""

    def __init__(self, registry: ToolRegistry):
        self._registry = registry

    @property
    def available(self) -> list[str]:
        return self._registry.names()

    def get(self, name: ToolName) -> IAgentTool | None:
        return self._registry.get(name)

    async def run(
        self,
        name: ToolName,
        user_id: UUID,
        agent_name: str,
        parameters: dict | None = None,
    ) -> ToolResult:
        return await self._registry.execute(
            name,
            ToolContext(
                user_id=user_id,
                agent_name=agent_name,
                parameters=parameters or {},
            ),
        )

    def register(self, tool: IAgentTool) -> None:
        self._registry.register(tool)
