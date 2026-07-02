"""GeekJob job source adapter."""

from uuid import uuid4

import httpx

from ugra.core.logging.setup import get_logger
from ugra.core.retry import async_retry
from ugra.domain.entities import JobSource, JobVacancy
from ugra.domain.value_objects import JobFilter
from ugra.infrastructure.adapters.job_sources.base import JobSourceAdapter

logger = get_logger(__name__)

GEEKJOB_API = "https://geekjob.ru/json/find/vacancy"


class GeekJobAdapter(JobSourceAdapter):
    def __init__(self, api_token: str = ""):
        self._token = api_token

    @property
    def source_name(self) -> str:
        return JobSource.GEEKJOB.value

    @async_retry()
    async def search(self, filters: JobFilter) -> list[JobVacancy]:
        params: dict[str, str | int] = {"page": 1}
        if filters.keywords:
            params["position"] = " ".join(filters.keywords)

        headers = {"User-Agent": "Ugra/0.1"}
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(GEEKJOB_API, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()

        vacancies: list[JobVacancy] = []
        for item in data if isinstance(data, list) else data.get("vacancies", []):
            vacancies.append(
                JobVacancy(
                    id=uuid4(),
                    external_id=str(item.get("id", "")),
                    source=JobSource.GEEKJOB,
                    title=item.get("position", ""),
                    company=item.get("company", {}).get("title", ""),
                    url=item.get("link", ""),
                    salary_from=item.get("salary", {}).get("from"),
                    salary_to=item.get("salary", {}).get("to"),
                    is_remote=item.get("remote", False),
                )
            )

        logger.info("geekjob_search_completed", count=len(vacancies))
        return vacancies

    async def get_vacancy(self, external_id: str) -> JobVacancy | None:
        return None
