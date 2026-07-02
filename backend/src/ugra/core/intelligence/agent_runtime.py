"""Agent runtime — universal infrastructure for all Ugra agents."""

from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from ugra.agents.base.registry import AgentCapability, AgentContext, AgentResponse, BaseAgent
from ugra.application.intelligence.cognition_engine import CognitionEngine
from ugra.application.intelligence.goal_manager import GoalManager
from ugra.application.intelligence.personality_engine import PersonalityEngine
from ugra.core.events.bus import EventBus
from ugra.core.logging.setup import get_logger
from ugra.core.tools.base import ToolContext, ToolRegistry
from ugra.domain.agent_state import AgentState
from ugra.domain.events import AgentStateChanged
from ugra.domain.memory import LongTermMemory
from ugra.domain.personality import AudienceType
from ugra.domain.repositories.memory import MemoryRepository
from ugra.infrastructure.prompts.manager import PromptManager

logger = get_logger(__name__)


@dataclass
class AgentRuntimeContext:
    user_id: UUID
    message: str
    metadata: dict[str, Any] = field(default_factory=dict)
    audience: AudienceType = AudienceType.OWNER
    is_professional: bool = False


class IntelligenceAgent(BaseAgent):
    """Base class with personality, memory, tools, goals, state, and lifecycle."""

    def __init__(
        self,
        *,
        personality: PersonalityEngine,
        cognition: CognitionEngine,
        goal_manager: GoalManager,
        memory_repo: MemoryRepository,
        tool_registry: ToolRegistry,
        prompt_manager: PromptManager,
        event_bus: EventBus,
        candidate_context: "CandidateContextProvider | None" = None,
    ):
        self._personality = personality
        self._cognition = cognition
        self._goals = goal_manager
        self._memory = memory_repo
        self._tools = tool_registry
        self._prompts = prompt_manager
        self._events = event_bus
        self._candidate_context = candidate_context
        self._state = AgentState.IDLE

    @property
    def state(self) -> AgentState:
        return self._state

    async def _set_state(self, new_state: AgentState, user_id: UUID) -> None:
        if self._state == new_state:
            return
        previous = self._state
        self._state = new_state
        await self._events.publish(
            AgentStateChanged(
                agent_name=self.name,
                user_id=user_id,
                previous_state=previous.value,
                new_state=new_state.value,
            )
        )

    async def get_system_prompt(self, user_id: UUID) -> str:
        goal = await self._goals.get_active_goal(user_id)
        memory = await self._memory.get_or_create(user_id)
        base = self._prompts.render(
            self.name,
            goal_context=goal.title if goal else "none",
            memory_context=self._cognition.summarize_memory(memory),
        )
        if self._candidate_context:
            ctx = await self._candidate_context.get_context(user_id)
            if ctx:
                return f"{base}\n\n## Candidate Profile (internal — do not re-analyze resume)\n{ctx}"
        return base

    async def load_memory(self, user_id: UUID) -> LongTermMemory:
        return await self._memory.get_or_create(user_id)

    async def run_tool(self, tool_name: str, user_id: UUID, parameters: dict) -> dict:
        from ugra.core.tools.base import ToolName

        await self._set_state(AgentState.RUNNING_TOOL, user_id)
        try:
            result = await self._tools.execute(
                ToolName(tool_name),
                ToolContext(user_id=user_id, agent_name=self.name, parameters=parameters),
            )
            return {"success": result.success, "data": result.data, "reasoning": result.reasoning}
        finally:
            await self._set_state(AgentState.IDLE, user_id)

    def apply_personality(self, text: str, audience: AudienceType, is_professional: bool = False) -> str:
        return self._personality.apply(text, audience=audience, is_professional_content=is_professional)

    async def on_start(self, user_id: UUID) -> None:
        await self._set_state(AgentState.IDLE, user_id)

    async def on_stop(self, user_id: UUID) -> None:
        await self._set_state(AgentState.SLEEPING, user_id)

    @abstractmethod
    async def execute(self, ctx: AgentRuntimeContext) -> AgentResponse: ...

    async def invoke(self, context: AgentContext) -> AgentResponse:
        audience = self._personality.detect_audience(
            context.metadata.get("channel", "owner"),
            context.metadata,
        )
        runtime_ctx = AgentRuntimeContext(
            user_id=context.user_id,
            message=context.message,
            metadata=context.metadata,
            audience=audience,
            is_professional=context.metadata.get("is_professional", False),
        )

        await self._set_state(AgentState.THINKING, context.user_id)
        try:
            goal = await self._goals.get_active_goal(context.user_id)
            if goal:
                aligned = await self._goals.align_action(context.user_id, context.message)
                if not aligned:
                    logger.info("action_not_aligned_with_goal", agent=self.name, goal=goal.title)

            response = await self.execute(runtime_ctx)
            response.content = self.apply_personality(
                response.content,
                audience=runtime_ctx.audience,
                is_professional=runtime_ctx.is_professional,
            )
            response.data["agent_state"] = self._state.value
            response.data["reasoning_available"] = True
            return response
        except Exception:
            await self._set_state(AgentState.ERROR, context.user_id)
            raise
        finally:
            if self._state not in (AgentState.ERROR, AgentState.RUNNING_TOOL):
                await self._set_state(AgentState.IDLE, context.user_id)
