"""PostgreSQL-backed long-term memory repository."""

import json
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ugra.domain.memory import (
    CommunicationRecord,
    CompanyPreference,
    InterviewRecord,
    LongTermMemory,
    OfferRecord,
    RecommendationRecord,
    RejectionRecord,
    TechnologyRecord,
    UserPreferences,
    VacancyRecord,
)
from ugra.domain.repositories.memory import MemoryRepository
from ugra.infrastructure.persistence.models.memory import MemoryModel


class PostgresMemoryRepository(MemoryRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory

    async def get_by_user(self, user_id: UUID) -> LongTermMemory | None:
        async with self._session_factory() as session:
            result = await session.execute(select(MemoryModel).where(MemoryModel.user_id == user_id))
            model = result.scalar_one_or_none()
            if not model:
                return None
            return self._to_domain(model)

    async def get_or_create(self, user_id: UUID) -> LongTermMemory:
        existing = await self.get_by_user(user_id)
        if existing:
            return existing
        memory = LongTermMemory(user_id=user_id)
        return await self.save(memory)

    async def save(self, memory: LongTermMemory) -> LongTermMemory:
        async with self._session_factory() as session:
            result = await session.execute(
                select(MemoryModel).where(MemoryModel.user_id == memory.user_id)
            )
            model = result.scalar_one_or_none()
            if not model:
                model = MemoryModel(user_id=memory.user_id)
                session.add(model)

            model.data_json = json.dumps(self._to_dict(memory), default=str)
            await session.commit()
            await session.refresh(model)
            return self._to_domain(model)

    def _to_dict(self, memory: LongTermMemory) -> dict:
        from dataclasses import asdict

        return asdict(memory)

    def _to_domain(self, model: MemoryModel) -> LongTermMemory:
        data = json.loads(model.data_json or "{}")
        return LongTermMemory(
            user_id=model.user_id,
            preferences=UserPreferences(**data.get("preferences", {})),
            resume_ids=[UUID(r) if isinstance(r, str) else r for r in data.get("resume_ids", [])],
            vacancy_history=[VacancyRecord(**v) for v in data.get("vacancy_history", [])],
            interview_history=[InterviewRecord(**i) for i in data.get("interview_history", [])],
            offer_history=[OfferRecord(**o) for o in data.get("offer_history", [])],
            communication_history=[CommunicationRecord(**c) for c in data.get("communication_history", [])],
            favorite_companies=[CompanyPreference(**c) for c in data.get("favorite_companies", [])],
            ignored_companies=[CompanyPreference(**c) for c in data.get("ignored_companies", [])],
            learned_technologies=[TechnologyRecord(**t) for t in data.get("learned_technologies", [])],
            recommendations=[RecommendationRecord(**r) for r in data.get("recommendations", [])],
            rejection_reasons=[RejectionRecord(**r) for r in data.get("rejection_reasons", [])],
        )


class InMemoryMemoryRepository(MemoryRepository):
    """Fallback for tests and development without DB."""

    def __init__(self) -> None:
        self._store: dict[UUID, LongTermMemory] = {}

    async def get_by_user(self, user_id: UUID) -> LongTermMemory | None:
        return self._store.get(user_id)

    async def get_or_create(self, user_id: UUID) -> LongTermMemory:
        if user_id not in self._store:
            self._store[user_id] = LongTermMemory(user_id=user_id)
        return self._store[user_id]

    async def save(self, memory: LongTermMemory) -> LongTermMemory:
        self._store[memory.user_id] = memory
        return memory
