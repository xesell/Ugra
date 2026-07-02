"""PostgreSQL goal repository."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ugra.domain.goals import Goal, GoalStatus, GoalType
from ugra.domain.repositories.goals import GoalRepository
from ugra.infrastructure.persistence.models.memory import GoalModel


class PostgresGoalRepository(GoalRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory

    async def get_by_id(self, goal_id: UUID) -> Goal | None:
        async with self._session_factory() as session:
            result = await session.execute(select(GoalModel).where(GoalModel.id == goal_id))
            model = result.scalar_one_or_none()
            return self._to_domain(model) if model else None

    async def get_by_user(self, user_id: UUID) -> list[Goal]:
        async with self._session_factory() as session:
            result = await session.execute(select(GoalModel).where(GoalModel.user_id == user_id))
            return [self._to_domain(m) for m in result.scalars().all()]

    async def save(self, goal: Goal) -> Goal:
        async with self._session_factory() as session:
            result = await session.execute(select(GoalModel).where(GoalModel.id == goal.id))
            model = result.scalar_one_or_none()
            if not model:
                model = GoalModel(id=goal.id, user_id=goal.user_id)
                session.add(model)

            model.title = goal.title
            model.description = goal.description
            model.goal_type = goal.goal_type.value
            model.status = goal.status.value
            model.priority = goal.priority
            model.target_value = goal.target_value
            model.progress = goal.progress
            model.updated_at = goal.updated_at

            await session.commit()
            await session.refresh(model)
            return self._to_domain(model)

    async def delete(self, goal_id: UUID) -> None:
        async with self._session_factory() as session:
            result = await session.execute(select(GoalModel).where(GoalModel.id == goal_id))
            model = result.scalar_one_or_none()
            if model:
                await session.delete(model)
                await session.commit()

    def _to_domain(self, model: GoalModel) -> Goal:
        return Goal(
            id=model.id,
            user_id=model.user_id,
            title=model.title,
            description=model.description,
            goal_type=GoalType(model.goal_type),
            status=GoalStatus(model.status),
            priority=model.priority,
            target_value=model.target_value,
            progress=model.progress,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
