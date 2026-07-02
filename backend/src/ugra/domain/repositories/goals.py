"""Goal repository port."""

from abc import ABC, abstractmethod
from uuid import UUID

from ugra.domain.goals import Goal


class GoalRepository(ABC):
    @abstractmethod
    async def get_by_id(self, goal_id: UUID) -> Goal | None: ...

    @abstractmethod
    async def get_by_user(self, user_id: UUID) -> list[Goal]: ...

    @abstractmethod
    async def save(self, goal: Goal) -> Goal: ...

    @abstractmethod
    async def delete(self, goal_id: UUID) -> None: ...
