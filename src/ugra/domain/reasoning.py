"""Internal reasoning — Ugra-owned decision explanations."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4


class ReasoningCategory(StrEnum):
    VACANCY_SELECTION = "vacancy_selection"
    RESUME_CHOICE = "resume_choice"
    APPLICATION_DECISION = "application_decision"
    SKILL_GAP = "skill_gap"
    LEARNING_PATH = "learning_path"
    GOAL_ALIGNMENT = "goal_alignment"
    TOOL_SELECTION = "tool_selection"
    GENERAL = "general"


@dataclass
class ReasoningRecord:
    id: UUID = field(default_factory=uuid4)
    agent_name: str = ""
    user_id: UUID = field(default_factory=uuid4)
    category: ReasoningCategory = ReasoningCategory.GENERAL
    decision: str = ""
    rationale: str = ""
    confidence: float = 0.0
    context: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
