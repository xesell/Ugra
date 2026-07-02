"""In-memory candidate profile storage (MVP — swap for Postgres later)."""

from uuid import UUID

from ugra.domain.candidate_profile import (
    AnalysisJob,
    AnalysisStatus,
    CandidateProfile,
    ProfileHistoryEntry,
    ResumeFile,
)
from ugra.domain.repositories.candidate_profile import (
    AnalysisJobStore,
    CandidateProfileRepository,
    ResumeFileRepository,
)


class InMemoryCandidateProfileRepository(CandidateProfileRepository):
    def __init__(self) -> None:
        self._profiles: dict[UUID, CandidateProfile] = {}
        self._history: dict[UUID, list[ProfileHistoryEntry]] = {}

    async def get_profile(self, user_id: UUID) -> CandidateProfile | None:
        return self._profiles.get(user_id)

    async def save_profile(self, profile: CandidateProfile) -> None:
        self._profiles[profile.user_id] = profile

    async def delete_profile(self, user_id: UUID) -> None:
        self._profiles.pop(user_id, None)

    async def get_history(self, user_id: UUID) -> list[ProfileHistoryEntry]:
        return list(self._history.get(user_id, []))

    async def add_history_entry(
        self, user_id: UUID, profile: CandidateProfile, trigger: str = "analysis"
    ) -> None:
        entry = ProfileHistoryEntry(
            version=profile.version,
            analyzed_at=profile.analyzed_at,
            model=profile.analysis_meta.model,
            duration_seconds=profile.analysis_meta.duration_seconds,
            changes_summary=f"v{profile.version} — {profile.identity.primary_specialization}",
            trigger=trigger,
        )
        self._history.setdefault(user_id, []).insert(0, entry)


class InMemoryResumeFileRepository(ResumeFileRepository):
    def __init__(self) -> None:
        self._files: dict[UUID, ResumeFile] = {}

    async def save_file(self, resume_file: ResumeFile) -> None:
        self._files[resume_file.id] = resume_file

    async def get_file(self, file_id: UUID) -> ResumeFile | None:
        return self._files.get(file_id)

    async def get_latest_for_user(self, user_id: UUID) -> ResumeFile | None:
        files = [f for f in self._files.values() if f.user_id == user_id]
        if not files:
            return None
        return max(files, key=lambda f: f.created_at)


class InMemoryAnalysisJobStore(AnalysisJobStore):
    def __init__(self) -> None:
        self._jobs: dict[UUID, AnalysisJob] = {}

    async def create(self, job: AnalysisJob) -> None:
        self._jobs[job.id] = job

    async def get(self, job_id: UUID) -> AnalysisJob | None:
        return self._jobs.get(job_id)

    async def update(self, job: AnalysisJob) -> None:
        self._jobs[job.id] = job

    async def get_active_for_user(self, user_id: UUID) -> AnalysisJob | None:
        active = [
            j
            for j in self._jobs.values()
            if j.user_id == user_id and j.status not in (AnalysisStatus.COMPLETED, AnalysisStatus.FAILED)
        ]
        return active[-1] if active else None
