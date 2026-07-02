"""PersonalityService — communication style, emotions, mode switching.

Alias: PersonalityEngine (legacy name).
"""

from ugra.application.intelligence.personality_engine import PersonalityEngine

# Canonical name from AI Core spec
PersonalityService = PersonalityEngine

__all__ = ["PersonalityService", "PersonalityEngine"]
