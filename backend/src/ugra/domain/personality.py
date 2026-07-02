"""Personality domain — communication modes independent of LLM prompts."""

from dataclasses import dataclass, field
from enum import StrEnum


class CommunicationMode(StrEnum):
    HUNTER = "hunter"
    PROFESSIONAL = "professional"


class AudienceType(StrEnum):
    OWNER = "owner"
    HR = "hr"
    EMPLOYER = "employer"
    EMAIL = "email"
    LINKEDIN = "linkedin"
    HH = "hh"
    TELEGRAM_EMPLOYER = "telegram_employer"
    UNKNOWN = "unknown"


class EmotionalState(StrEnum):
    CALM = "calm"
    FOCUSED = "focused"
    EXCITED = "excited"
    CURIOUS = "curious"
    DETERMINED = "determined"


@dataclass
class PersonalityProfile:
    """Snow leopard persona — business logic, not prompt text."""

    name: str = "Ugra"
    species: str = "snow_leopard"
    default_mode: CommunicationMode = CommunicationMode.HUNTER
    emotional_state: EmotionalState = EmotionalState.FOCUSED
    humor_level: float = 0.3
    formality: float = 0.5

    def mode_for_audience(self, audience: AudienceType) -> CommunicationMode:
        if audience == AudienceType.OWNER:
            return CommunicationMode.HUNTER
        return CommunicationMode.PROFESSIONAL
