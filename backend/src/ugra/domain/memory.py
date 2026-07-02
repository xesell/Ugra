"""Long-term memory entities — Ugra-owned knowledge about the user."""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class UserPreferences:
    preferred_roles: list[str] = field(default_factory=list)
    preferred_salary_min: int | None = None
    preferred_remote: bool = True
    preferred_countries: list[str] = field(default_factory=list)
    communication_style: str = "professional"
    ignored_keywords: list[str] = field(default_factory=list)


@dataclass
class VacancyRecord:
    job_id: UUID = field(default_factory=uuid4)
    title: str = ""
    company: str = ""
    match_score: float = 0.0
    status: str = "new"
    applied_at: datetime | None = None
    notes: str = ""


@dataclass
class InterviewRecord:
    id: UUID = field(default_factory=uuid4)
    job_id: UUID = field(default_factory=uuid4)
    company: str = ""
    scheduled_at: datetime | None = None
    outcome: str | None = None
    feedback: str = ""


@dataclass
class OfferRecord:
    id: UUID = field(default_factory=uuid4)
    job_id: UUID = field(default_factory=uuid4)
    company: str = ""
    salary: int | None = None
    currency: str = "RUB"
    status: str = "pending"
    received_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CommunicationRecord:
    id: UUID = field(default_factory=uuid4)
    channel: str = ""
    contact: str = ""
    summary: str = ""
    occurred_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CompanyPreference:
    company: str = ""
    reason: str = ""


@dataclass
class TechnologyRecord:
    name: str = ""
    proficiency: str = "beginner"
    learned_at: datetime | None = None


@dataclass
class RecommendationRecord:
    id: UUID = field(default_factory=uuid4)
    source: str = ""
    content: str = ""
    received_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class RejectionRecord:
    job_id: UUID | None = None
    company: str = ""
    reason: str = ""
    rejected_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class LongTermMemory:
    """Aggregate root for all persistent user knowledge."""

    user_id: UUID = field(default_factory=uuid4)
    preferences: UserPreferences = field(default_factory=UserPreferences)
    resume_ids: list[UUID] = field(default_factory=list)
    vacancy_history: list[VacancyRecord] = field(default_factory=list)
    interview_history: list[InterviewRecord] = field(default_factory=list)
    offer_history: list[OfferRecord] = field(default_factory=list)
    communication_history: list[CommunicationRecord] = field(default_factory=list)
    favorite_companies: list[CompanyPreference] = field(default_factory=list)
    ignored_companies: list[CompanyPreference] = field(default_factory=list)
    learned_technologies: list[TechnologyRecord] = field(default_factory=list)
    recommendations: list[RecommendationRecord] = field(default_factory=list)
    rejection_reasons: list[RejectionRecord] = field(default_factory=list)
    updated_at: datetime = field(default_factory=datetime.utcnow)
