"""Repository interfaces (ports)."""

from abc import ABC, abstractmethod
from uuid import UUID

from ugra.domain.entities import JobVacancy, Resume, UserProfile
from ugra.domain.value_objects import JobFilter


class UserRepository(ABC):
    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> UserProfile | None: ...

    @abstractmethod
    async def get_by_telegram_id(self, telegram_id: int) -> UserProfile | None: ...

    @abstractmethod
    async def save(self, user: UserProfile) -> UserProfile: ...


class JobRepository(ABC):
    @abstractmethod
    async def search(self, user_id: UUID, filters: JobFilter) -> list[JobVacancy]: ...

    @abstractmethod
    async def get_by_id(self, job_id: UUID) -> JobVacancy | None: ...

    @abstractmethod
    async def save(self, job: JobVacancy) -> JobVacancy: ...

    @abstractmethod
    async def get_top_matches(self, user_id: UUID, limit: int = 10) -> list[JobVacancy]: ...


class ResumeRepository(ABC):
    @abstractmethod
    async def get_by_user(self, user_id: UUID) -> list[Resume]: ...

    @abstractmethod
    async def get_by_id(self, resume_id: UUID) -> Resume | None: ...

    @abstractmethod
    async def save(self, resume: Resume) -> Resume: ...

    @abstractmethod
    async def find_best_match(self, user_id: UUID, job: JobVacancy) -> Resume | None: ...
