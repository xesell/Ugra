"""Context builder — assembles UnifiedAgentContext from repositories."""

from uuid import UUID

from ugra.agents.base.registry import AgentContext
from ugra.agents.runtime.context import UnifiedAgentContext
from ugra.agents.runtime.memory import AgentMemory
from ugra.application.intelligence.goal_manager import GoalManager
from ugra.application.intelligence.personality_service import PersonalityService


class ContextBuilder:
    """Builds full UnifiedAgentContext for every agent request."""

    def __init__(
        self,
        memory: AgentMemory,
        goals: GoalManager,
        personality: PersonalityService,
    ):
        self._memory = memory
        self._goals = goals
        self._personality = personality

    async def build(self, context: AgentContext) -> UnifiedAgentContext:
        audience = self._personality.detect_audience(
            context.metadata.get("channel", "owner"),
            context.metadata,
        )
        mode = self._personality.resolve_mode(audience)

        memory = await self._memory.load(context.user_id)
        goal = await self._goals.get_active_goal(context.user_id)

        unified = UnifiedAgentContext(
            user_id=context.user_id,
            message=context.message,
            user_name=context.metadata.get("user_name", ""),
            user_skills=context.metadata.get("skills", []),
            experience_years=context.metadata.get("experience_years", 0),
            current_resume=context.metadata.get("current_resume"),
            current_vacancy=context.metadata.get("current_vacancy"),
            current_goal=goal,
            memory=memory,
            audience=audience,
            communication_mode=mode,
            is_professional=context.metadata.get("is_professional", False),
            channel=context.metadata.get("channel", "owner"),
            metadata=context.metadata,
        )
        unified.add_turn("user", context.message)
        return unified
