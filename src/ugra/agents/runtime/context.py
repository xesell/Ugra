"""Unified agent context — single object for every agent request."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from ugra.domain.goals import Goal
from ugra.domain.memory import LongTermMemory
from ugra.domain.personality import AudienceType, CommunicationMode


@dataclass
class ConversationTurn:
    role: str
    content: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class UnifiedAgentContext:
    """Everything an agent needs for one request."""

    user_id: UUID
    message: str
    current_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # User profile snapshot
    user_name: str = ""
    user_skills: list[str] = field(default_factory=list)
    experience_years: int = 0

    # Active entities
    current_resume: dict[str, Any] | None = None
    current_vacancy: dict[str, Any] | None = None
    current_goal: Goal | None = None

    # Memory & conversation
    memory: LongTermMemory | None = None
    conversation: list[ConversationTurn] = field(default_factory=list)

    # Communication
    audience: AudienceType = AudienceType.OWNER
    communication_mode: CommunicationMode = CommunicationMode.HUNTER
    is_professional: bool = False
    channel: str = "owner"

    # Extra metadata from transport layer
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def skills(self) -> list[str]:
        if self.user_skills:
            return self.user_skills
        return self.metadata.get("skills", [])

    @property
    def filters(self) -> dict[str, Any]:
        return self.metadata.get("filters", {})

    def add_turn(self, role: str, content: str) -> None:
        self.conversation.append(ConversationTurn(role=role, content=content))
