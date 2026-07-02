"""Provides candidate prompt context to all AI modules."""

from uuid import UUID

from ugra.domain.repositories.candidate_profile import CandidateProfileRepository


class CandidateContextProvider:
    def __init__(self, profile_repo: CandidateProfileRepository):
        self._profiles = profile_repo

    async def get_context(self, user_id: UUID) -> str:
        profile = await self._profiles.get_profile(user_id)
        if not profile or not profile.prompt_context:
            return ""
        return profile.prompt_context

    async def get_profile(self, user_id: UUID):
        return await self._profiles.get_profile(user_id)
