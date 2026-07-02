"""Goal manager — aligns agent actions to user goals."""

from uuid import UUID

from ugra.core.events.bus import EventBus
from ugra.core.logging.setup import get_logger
from ugra.domain.events import GoalProgressUpdated
from ugra.domain.goals import Goal, GoalStatus, GoalType
from ugra.domain.repositories.goals import GoalRepository

logger = get_logger(__name__)


class GoalManager:
    def __init__(self, repository: GoalRepository, event_bus: EventBus):
        self._repo = repository
        self._event_bus = event_bus

    async def get_active_goal(self, user_id: UUID) -> Goal | None:
        goals = await self._repo.get_by_user(user_id)
        active = [g for g in goals if g.is_active()]
        if not active:
            return None
        return max(active, key=lambda g: g.priority)

    async def set_goal(
        self,
        user_id: UUID,
        title: str,
        goal_type: GoalType = GoalType.CUSTOM,
        description: str = "",
    ) -> Goal:
        existing = await self.get_active_goal(user_id)
        if existing:
            existing.status = GoalStatus.PAUSED
            await self._repo.save(existing)

        goal = Goal(
            user_id=user_id,
            title=title,
            description=description,
            goal_type=goal_type,
            status=GoalStatus.ACTIVE,
        )
        saved = await self._repo.save(goal)
        logger.info("goal_set", user_id=str(user_id), title=title)
        return saved

    async def update_progress(self, goal_id: UUID, user_id: UUID, progress: float) -> Goal:
        goal = await self._repo.get_by_id(goal_id)
        if not goal:
            raise ValueError(f"Goal {goal_id} not found")

        goal.progress = min(max(progress, 0.0), 1.0)
        if goal.progress >= 1.0:
            goal.status = GoalStatus.COMPLETED

        saved = await self._repo.save(goal)
        await self._event_bus.publish(
            GoalProgressUpdated(goal_id=goal_id, user_id=user_id, progress=goal.progress)
        )
        return saved

    async def align_action(self, user_id: UUID, action: str) -> bool:
        goal = await self.get_active_goal(user_id)
        if not goal:
            return True
        keywords = {
            GoalType.FIND_JOB: ["job", "vacancy", "search", "apply", "ваканс"],
            GoalType.SALARY_INCREASE: ["salary", "offer", "зарплат"],
            GoalType.INTERVIEW_PREP: ["interview", "собесед"],
            GoalType.LEARN_SKILL: ["learn", "study", "skill", "изуч"],
        }
        relevant = keywords.get(goal.goal_type, [])
        if not relevant:
            return True
        action_lower = action.lower()
        return any(k in action_lower for k in relevant)
