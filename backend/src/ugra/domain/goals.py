"""Goal system — every agent action is aligned to a user goal."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4


class GoalStatus(StrEnum):
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    FAILED = "failed"


class GoalType(StrEnum):
    FIND_JOB = "find_job"
    SALARY_INCREASE = "salary_increase"
    INTERVIEW_PREP = "interview_prep"
    LEARN_SKILL = "learn_skill"
    CUSTOM = "custom"


@dataclass
class Goal:
    id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    title: str = ""
    description: str = ""
    goal_type: GoalType = GoalType.CUSTOM
    status: GoalStatus = GoalStatus.ACTIVE
    priority: int = 1
    target_value: str | None = None
    progress: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def is_active(self) -> bool:
        return self.status == GoalStatus.ACTIVE
