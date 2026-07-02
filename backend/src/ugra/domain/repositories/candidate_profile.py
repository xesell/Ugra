"""Candidate profile repository port."""

from abc import ABC, abstractmethod
from uuid import UUID

from ugra.domain.candidate_profile import AnalysisJob, CandidateProfile, ResumeFile


class CandidateProfileRepository(ABC):
    @abstractmethod
    async def get_profile(self, user_id: UUID) -> CandidateProfile | None: ...

    @abstractmethod
    async def save_profile(self, profile: CandidateProfile) -> None: ...

    @abstractmethod
    async def delete_profile(self, user_id: UUID) -> None: ...

    @abstractmethod
    async def get_history(self, user_id: UUID) -> list: ...

    @abstractmethod
    async def add_history_entry(self, user_id: UUID, profile: CandidateProfile, trigger: str) -> None: ...


class ResumeFileRepository(ABC):
    @abstractmethod
    async def save_file(self, resume_file: ResumeFile) -> None: ...

    @abstractmethod
    async def get_file(self, file_id: UUID) -> ResumeFile | None: ...

    @abstractmethod
    async def get_latest_for_user(self, user_id: UUID) -> ResumeFile | None: ...


class AnalysisJobStore(ABC):
    @abstractmethod
    async def create(self, job: AnalysisJob) -> None: ...

    @abstractmethod
    async def get(self, job_id: UUID) -> AnalysisJob | None: ...

    @abstractmethod
    async def update(self, job: AnalysisJob) -> None: ...

    @abstractmethod
    async def get_active_for_user(self, user_id: UUID) -> AnalysisJob | None: ...
