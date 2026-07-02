"""Domain events for event-driven architecture."""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass(frozen=True)
class DomainEvent:
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class JobAnalyzed(DomainEvent):
    job_id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    match_score: float = 0.0


@dataclass(frozen=True)
class VacancyFound(DomainEvent):
    job_id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    title: str = ""
    company: str = ""
    match_score: float = 0.0


@dataclass(frozen=True)
class ApplicationSubmitted(DomainEvent):
    job_id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    resume_id: UUID = field(default_factory=uuid4)


@dataclass(frozen=True)
class InterviewReceived(DomainEvent):
    job_id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    scheduled_at: datetime | None = None


@dataclass(frozen=True)
class InterviewScheduled(DomainEvent):
    job_id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)


@dataclass(frozen=True)
class OfferReceived(DomainEvent):
    job_id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    salary: int | None = None


@dataclass(frozen=True)
class ResumeUpdated(DomainEvent):
    resume_id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    version: int = 1


@dataclass(frozen=True)
class SkillGapDetected(DomainEvent):
    user_id: UUID = field(default_factory=uuid4)
    job_id: UUID = field(default_factory=uuid4)
    missing_skills: tuple[str, ...] = ()


@dataclass(frozen=True)
class LearningCompleted(DomainEvent):
    user_id: UUID = field(default_factory=uuid4)
    skill: str = ""


@dataclass(frozen=True)
class NotificationSent(DomainEvent):
    user_id: UUID = field(default_factory=uuid4)
    channel: str = ""
    message: str = ""


@dataclass(frozen=True)
class AgentStateChanged(DomainEvent):
    agent_name: str = ""
    user_id: UUID = field(default_factory=uuid4)
    previous_state: str = ""
    new_state: str = ""


@dataclass(frozen=True)
class GoalProgressUpdated(DomainEvent):
    goal_id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    progress: float = 0.0
