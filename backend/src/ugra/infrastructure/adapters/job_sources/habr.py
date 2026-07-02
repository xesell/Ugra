"""Habr Career job source adapter (stub with extensible interface)."""

from uuid import uuid4

import httpx

from ugra.core.logging.setup import get_logger
from ugra.core.retry import async_retry
from ugra.domain.entities import JobSource, JobVacancy
from ugra.domain.value_objects import JobFilter
from ugra.infrastructure.adapters.job_sources.base import JobSourceAdapter

logger = get_logger(__name__)


class HabrCareerAdapter(JobSourceAdapter):
    @property
    def source_name(self) -> str:
        return JobSource.HABR_CAREER.value

    @async_retry()
    async def search(self, filters: JobFilter) -> list[JobVacancy]:
        # Habr Career public API is limited; adapter ready for scraping/API integration
        logger.info("habr_career_search", keywords=filters.keywords)
        return []

    async def get_vacancy(self, external_id: str) -> JobVacancy | None:
        return JobVacancy(
            id=uuid4(),
            external_id=external_id,
            source=JobSource.HABR_CAREER,
        )
