"""AgentMemory — facade over long-term memory repository."""

from uuid import UUID

from ugra.domain.memory import (
    CommunicationRecord,
    CompanyPreference,
    InterviewRecord,
    LongTermMemory,
    OfferRecord,
    RejectionRecord,
    TechnologyRecord,
    VacancyRecord,
)
from ugra.domain.repositories.memory import MemoryRepository


class AgentMemory:
    """Agent-facing memory API. Persists to PostgreSQL via repository."""

    def __init__(self, repository: MemoryRepository):
        self._repo = repository

    async def load(self, user_id: UUID) -> LongTermMemory:
        return await self._repo.get_or_create(user_id)

    async def save(self, memory: LongTermMemory) -> LongTermMemory:
        return await self._repo.save(memory)

    async def record_vacancy(
        self,
        user_id: UUID,
        job_id: UUID,
        title: str,
        company: str,
        match_score: float,
        status: str = "found",
    ) -> LongTermMemory:
        memory = await self.load(user_id)
        existing_ids = {v.job_id for v in memory.vacancy_history}
        if job_id not in existing_ids:
            memory.vacancy_history.append(
                VacancyRecord(
                    job_id=job_id,
                    title=title,
                    company=company,
                    match_score=match_score,
                    status=status,
                )
            )
            return await self.save(memory)
        return memory

    async def record_rejection(
        self, user_id: UUID, job_id: UUID, company: str, reason: str
    ) -> LongTermMemory:
        memory = await self.load(user_id)
        memory.rejection_reasons.append(
            RejectionRecord(job_id=job_id, company=company, reason=reason)
        )
        return await self.save(memory)

    async def record_interview(
        self, user_id: UUID, job_id: UUID, company: str
    ) -> LongTermMemory:
        memory = await self.load(user_id)
        memory.interview_history.append(InterviewRecord(job_id=job_id, company=company))
        return await self.save(memory)

    async def record_offer(
        self, user_id: UUID, job_id: UUID, company: str, salary: int | None = None
    ) -> LongTermMemory:
        memory = await self.load(user_id)
        memory.offer_history.append(
            OfferRecord(job_id=job_id, company=company, salary=salary)
        )
        return await self.save(memory)

    async def record_conversation(
        self, user_id: UUID, channel: str, contact: str, summary: str
    ) -> LongTermMemory:
        memory = await self.load(user_id)
        memory.communication_history.append(
            CommunicationRecord(channel=channel, contact=contact, summary=summary)
        )
        return await self.save(memory)

    async def ignore_company(self, user_id: UUID, company: str, reason: str) -> LongTermMemory:
        memory = await self.load(user_id)
        memory.ignored_companies.append(CompanyPreference(company=company, reason=reason))
        return await self.save(memory)

    async def favorite_company(self, user_id: UUID, company: str, reason: str) -> LongTermMemory:
        memory = await self.load(user_id)
        memory.favorite_companies.append(CompanyPreference(company=company, reason=reason))
        return await self.save(memory)

    async def learn_technology(self, user_id: UUID, name: str, proficiency: str = "beginner") -> LongTermMemory:
        memory = await self.load(user_id)
        memory.learned_technologies.append(TechnologyRecord(name=name, proficiency=proficiency))
        return await self.save(memory)
