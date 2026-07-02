"""User corrections to candidate profile — user overrides AI."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from ugra.application.candidate.prompt_context import build_prompt_context
from ugra.domain.candidate_profile import (
    CandidateProfile,
    ProfileHistoryEntry,
    RolePriority,
    SearchStrategy,
    SpecialistLevel,
)
from ugra.domain.repositories.candidate_profile import CandidateProfileRepository


class CandidateProfileService:
    def __init__(self, profile_repo: CandidateProfileRepository):
        self._profiles = profile_repo

    async def get_profile(self, user_id: UUID) -> CandidateProfile | None:
        return await self._profiles.get_profile(user_id)

    async def get_history(self, user_id: UUID) -> list[ProfileHistoryEntry]:
        return await self._profiles.get_history(user_id)

    async def update_profile(self, user_id: UUID, updates: dict) -> CandidateProfile:
        profile = await self._profiles.get_profile(user_id)
        if not profile:
            raise ValueError("Profile not found")

        changes: list[str] = []

        if "primary_specialization" in updates and updates["primary_specialization"]:
            old = profile.identity.primary_specialization
            profile.identity.primary_specialization = updates["primary_specialization"].strip()
            if old != profile.identity.primary_specialization:
                changes.append(
                    f"Специализация: {old} → {profile.identity.primary_specialization}"
                )

        if "level" in updates and updates["level"]:
            try:
                new_level = SpecialistLevel(updates["level"])
                if profile.identity.level != new_level:
                    changes.append(f"Уровень: {profile.identity.level.value} → {new_level.value}")
                    profile.identity.level = new_level
            except ValueError:
                pass

        if "preferred_roles" in updates and updates["preferred_roles"] is not None:
            profile.preferred_roles = [
                RolePriority(title=r.get("title", ""), priority=r.get("priority", "medium"))
                for r in updates["preferred_roles"]
                if r.get("title")
            ]
            changes.append("Обновлены приоритетные роли")

        if "exclude_keywords" in updates and updates["exclude_keywords"] is not None:
            profile.search_strategy.exclude_keywords = list(updates["exclude_keywords"])
            changes.append("Обновлён список исключений поиска")

        if "include_keywords" in updates and updates["include_keywords"] is not None:
            profile.search_strategy.include_keywords = list(updates["include_keywords"])
            changes.append("Обновлены ключевые слова поиска")

        if "excluded_roles" in updates and updates["excluded_roles"] is not None:
            profile.search_strategy.excluded_roles = list(updates["excluded_roles"])
            changes.append("Обновлён список нежелательных ролей")

        profile.prompt_context = build_prompt_context(profile)
        profile.version += 1
        profile.analyzed_at = datetime.now(timezone.utc)

        summary = "; ".join(changes) if changes else "Ручная корректировка"
        await self._profiles.save_profile(profile)
        await self._profiles.add_history_entry(
            user_id,
            profile,
            trigger=f"user_edit: {summary}",
        )
        return profile
