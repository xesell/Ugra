"""In-memory goal repository — swap for PostgreSQL in production."""

from uuid import UUID

from ugra.domain.goals import Goal
from ugra.domain.repositories.goals import GoalRepository


class InMemoryGoalRepository(GoalRepository):
    def __init__(self) -> None:
        self._store: dict[UUID, Goal] = {}

    async def get_by_id(self, goal_id: UUID) -> Goal | None:
        return self._store.get(goal_id)

    async def get_by_user(self, user_id: UUID) -> list[Goal]:
        return [g for g in self._store.values() if g.user_id == user_id]

    async def save(self, goal: Goal) -> Goal:
        self._store[goal.id] = goal
        return goal

    async def delete(self, goal_id: UUID) -> None:
        self._store.pop(goal_id, None)
