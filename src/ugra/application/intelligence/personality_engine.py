"""Personality Engine — independent business logic, not part of LLM prompts."""

import random
import re

from ugra.domain.personality import (
    AudienceType,
    CommunicationMode,
    EmotionalState,
    PersonalityProfile,
)


HUNTER_EXPRESSIONS = [
    "Мур...",
    "Ррр...",
    "Укушу.",
    "Кажется, я вышла на след.",
    "Смотри кого поймала.",
]

FORBIDDEN_IN_PROFESSIONAL = [
    "мур",
    "ррр",
    "укушу",
    "след",
    "поймала",
    "барс",
    "звер",
    "ai",
    "искусственн",
    "бот",
    "chatgpt",
    "llm",
]


class PersonalityEngine:
    """Transforms agent output based on personality rules — separate from prompts."""

    def __init__(self, profile: PersonalityProfile | None = None):
        self._profile = profile or PersonalityProfile()

    @property
    def profile(self) -> PersonalityProfile:
        return self._profile

    def detect_audience(self, channel: str, metadata: dict | None = None) -> AudienceType:
        metadata = metadata or {}
        if metadata.get("is_owner", False) or channel in ("telegram_owner", "owner"):
            return AudienceType.OWNER
        mapping = {
            "email": AudienceType.EMAIL,
            "linkedin": AudienceType.LINKEDIN,
            "hh": AudienceType.HH,
            "hr": AudienceType.HR,
            "telegram_employer": AudienceType.TELEGRAM_EMPLOYER,
        }
        return mapping.get(channel.lower(), AudienceType.UNKNOWN)

    def resolve_mode(self, audience: AudienceType) -> CommunicationMode:
        return self._profile.mode_for_audience(audience)

    def react_to_event(self, event_type: str) -> EmotionalState:
        reactions = {
            "VacancyFound": EmotionalState.EXCITED,
            "OfferReceived": EmotionalState.EXCITED,
            "SkillGapDetected": EmotionalState.CURIOUS,
            "InterviewReceived": EmotionalState.DETERMINED,
            "error": EmotionalState.FOCUSED,
        }
        return reactions.get(event_type, EmotionalState.CALM)

    def apply(
        self,
        text: str,
        *,
        audience: AudienceType,
        is_professional_content: bool = False,
    ) -> str:
        mode = self.resolve_mode(audience)

        if mode == CommunicationMode.PROFESSIONAL or is_professional_content:
            return self._apply_professional(text)

        return self._apply_hunter(text)

    def _apply_professional(self, text: str) -> str:
        result = text
        for forbidden in FORBIDDEN_IN_PROFESSIONAL:
            result = re.sub(re.escape(forbidden), "", result, flags=re.IGNORECASE)
        result = re.sub(r"\s{2,}", " ", result).strip()
        return result

    def _apply_hunter(self, text: str) -> str:
        if self._profile.humor_level < 0.2:
            return text

        if random.random() < 0.15 and len(text) > 50:
            expression = random.choice(HUNTER_EXPRESSIONS)
            if expression.endswith("."):
                return f"{expression} {text}"
            return f"{text}\n\n_{expression}_"

        return text

    def greeting(self, audience: AudienceType) -> str:
        if self.resolve_mode(audience) == CommunicationMode.HUNTER:
            return "Мур... Привет! Я Ugra — твой охотник за карьерой."
        return "Здравствуйте."
