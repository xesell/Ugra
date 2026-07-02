"""Internal candidate profile — single source of truth after resume analysis."""

from __future__ import annotations

from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4


class AnalysisStatus(StrEnum):
    PENDING = "pending"
    EXTRACTING = "extracting"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"


class SpecialistLevel(StrEnum):
    JUNIOR = "junior"
    MIDDLE = "middle"
    SENIOR = "senior"
    LEAD = "lead"
    ARCHITECT = "architect"


@dataclass
class TechSkill:
    name: str
    category: str
    confidence: float  # 0-100


@dataclass
class RolePriority:
    title: str
    priority: str  # high | medium | low


@dataclass
class ExperienceBreakdown:
    total_years: float = 0.0
    commercial_years: float = 0.0
    leadership_years: float = 0.0
    architecture_years: float = 0.0
    ai_years: float = 0.0
    devops_years: float = 0.0
    backend_years: float = 0.0
    frontend_years: float = 0.0
    analytics_years: float = 0.0


@dataclass
class SearchStrategy:
    include_keywords: list[str] = field(default_factory=list)
    exclude_keywords: list[str] = field(default_factory=list)
    preferred_roles: list[str] = field(default_factory=list)
    excluded_roles: list[str] = field(default_factory=list)


@dataclass
class CandidateIdentity:
    full_name: str = ""
    primary_specialization: str = ""
    secondary_specializations: list[str] = field(default_factory=list)
    level: SpecialistLevel = SpecialistLevel.MIDDLE
    level_rationale: str = ""


@dataclass
class AnalysisMeta:
    model: str = ""
    provider: str = ""
    duration_seconds: float = 0.0
    resume_filename: str = ""


@dataclass
class AnalysisStats:
    skills_count: int = 0
    technologies_count: int = 0
    companies_count: int = 0
    projects_count: int = 0
    domains_count: int = 0
    roles_count: int = 0


@dataclass
class ProfileHistoryEntry:
    version: int
    analyzed_at: datetime
    model: str
    duration_seconds: float = 0.0
    changes_summary: str = ""
    trigger: str = "analysis"


@dataclass
class CandidateProfile:
    """Unified internal representation of the candidate — not user-editable."""

    user_id: UUID
    identity: CandidateIdentity
    experience: ExperienceBreakdown
    skills: list[TechSkill] = field(default_factory=list)
    domains: list[str] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    preferred_roles: list[RolePriority] = field(default_factory=list)
    search_strategy: SearchStrategy = field(default_factory=SearchStrategy)
    prompt_context: str = ""
    ai_summary: list[str] = field(default_factory=list)
    analysis_meta: AnalysisMeta = field(default_factory=AnalysisMeta)
    analysis_stats: AnalysisStats = field(default_factory=AnalysisStats)
    resume_file_id: UUID | None = None
    version: int = 1
    analyzed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def flat_skills(self) -> list[str]:
        return [s.name for s in sorted(self.skills, key=lambda x: -x.confidence)]

    def top_skills(self, limit: int = 20) -> list[str]:
        return [s.name for s in sorted(self.skills, key=lambda x: -x.confidence)[:limit]]

    def experience_years(self) -> int:
        return int(self.experience.commercial_years or self.experience.total_years)

    def to_dict(self) -> dict[str, Any]:
        from dataclasses import asdict

        data = asdict(self)
        data["user_id"] = str(self.user_id)
        data["resume_file_id"] = str(self.resume_file_id) if self.resume_file_id else None
        data["analyzed_at"] = self.analyzed_at.isoformat()
        data["identity"]["level"] = self.identity.level.value
        data["analysis_meta"] = {
            "model": self.analysis_meta.model,
            "provider": self.analysis_meta.provider,
            "duration_seconds": self.analysis_meta.duration_seconds,
            "resume_filename": self.analysis_meta.resume_filename,
        }
        data["analysis_stats"] = asdict(self.analysis_stats)
        return data


@dataclass
class ResumeFile:
    id: UUID
    user_id: UUID
    filename: str
    storage_path: str
    extracted_text: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class AnalysisJob:
    id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    resume_file_id: UUID | None = None
    status: AnalysisStatus = AnalysisStatus.PENDING
    current_step: str = ""
    steps_completed: list[str] = field(default_factory=list)
    progress: int = 0
    error: str = ""
    profile: CandidateProfile | None = None
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_status_dict(self) -> dict[str, Any]:
        return {
            "job_id": str(self.id),
            "status": self.status.value,
            "current_step": self.current_step,
            "steps_completed": self.steps_completed,
            "progress": self.progress,
            "error": self.error,
            "profile_ready": self.profile is not None,
        }


ANALYSIS_STEPS = [
    ("extract_text", "Извлекаю текст"),
    ("analyze_experience", "Анализирую опыт"),
    ("determine_specialization", "Определяю специализацию"),
    ("build_skills_map", "Строю карту навыков"),
    ("analyze_career", "Анализирую карьерный путь"),
    ("build_search_strategy", "Формирую поисковую стратегию"),
    ("create_profile", "Создаю профиль кандидата"),
    ("configure_ai", "Настраиваю AI"),
]
