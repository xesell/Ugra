"""Domain entities."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4


class JobSource(StrEnum):
    HH_RU = "hh.ru"
    HH_KZ = "hh.kz"
    HABR_CAREER = "habr_career"
    GEEKJOB = "geekjob"


class ExperienceLevel(StrEnum):
    INTERN = "intern"
    JUNIOR = "junior"
    MIDDLE = "middle"
    SENIOR = "senior"
    LEAD = "lead"
    ARCHITECT = "architect"


class ApplicationStatus(StrEnum):
    NEW = "new"
    ANALYZED = "analyzed"
    APPLIED = "applied"
    INTERVIEW = "interview"
    REJECTED = "rejected"
    OFFER = "offer"


@dataclass
class UserProfile:
    id: UUID = field(default_factory=uuid4)
    telegram_id: int | None = None
    full_name: str = ""
    email: str = ""
    skills: list[str] = field(default_factory=list)
    experience_years: int = 0
    preferred_level: ExperienceLevel = ExperienceLevel.MIDDLE
    preferred_remote: bool = True
    preferred_countries: list[str] = field(default_factory=list)
    english_level: str = "B1"
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class JobVacancy:
    id: UUID = field(default_factory=uuid4)
    external_id: str = ""
    source: JobSource = JobSource.HH_RU
    title: str = ""
    company: str = ""
    description: str = ""
    url: str = ""
    salary_from: int | None = None
    salary_to: int | None = None
    currency: str = "RUB"
    is_remote: bool = False
    country: str = ""
    technologies: list[str] = field(default_factory=list)
    required_skills: list[str] = field(default_factory=list)
    preferred_skills: list[str] = field(default_factory=list)
    experience_level: ExperienceLevel | None = None
    requires_relocation: bool = False
    requires_english: bool = False
    match_score: float | None = None
    pros: list[str] = field(default_factory=list)
    cons: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Resume:
    id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    title: str = ""
    content: str = ""
    skills: list[str] = field(default_factory=list)
    is_default: bool = False
    version: int = 1
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CoverLetter:
    id: UUID = field(default_factory=uuid4)
    job_id: UUID = field(default_factory=uuid4)
    resume_id: UUID = field(default_factory=uuid4)
    content: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SkillGap:
    missing_skills: list[str] = field(default_factory=list)
    recommended_resources: list[str] = field(default_factory=list)


@dataclass
class LearningRoadmap:
    id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    job_id: UUID | None = None
    skills: list[str] = field(default_factory=list)
    steps: list[str] = field(default_factory=list)
    estimated_weeks: int = 0


@dataclass
class InterviewPrep:
    id: UUID = field(default_factory=uuid4)
    job_id: UUID = field(default_factory=uuid4)
    questions: list[str] = field(default_factory=list)
    answers: list[str] = field(default_factory=list)
    topics: list[str] = field(default_factory=list)
    checklist: list[str] = field(default_factory=list)
