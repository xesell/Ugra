"""HH.ru / HH.kz job source adapter."""

from uuid import uuid4

import httpx

from ugra.core.logging.setup import get_logger
from ugra.core.retry import async_retry
from ugra.domain.entities import ExperienceLevel, JobSource, JobVacancy
from ugra.domain.value_objects import JobFilter
from ugra.infrastructure.adapters.job_sources.base import JobSourceAdapter

logger = get_logger(__name__)

HH_API_BASE = "https://api.hh.ru"


class HeadHunterAdapter(JobSourceAdapter):
    def __init__(self, api_token: str = "", country: str = "113", source: JobSource = JobSource.HH_RU):
        self._token = api_token
        self._area = country  # 113=Russia, 40=Kazakhstan
        self._source = source

    @property
    def source_name(self) -> str:
        return self._source.value

    @async_retry()
    async def search(self, filters: JobFilter) -> list[JobVacancy]:
        params: dict[str, str | int] = {
            "area": self._area,
            "per_page": 20,
            "page": 0,
        }
        if filters.keywords:
            params["text"] = " ".join(filters.keywords)
        if filters.salary_min:
            params["salary"] = filters.salary_min
        if filters.remote_only:
            params["schedule"] = "remote"

        headers = {"User-Agent": "Ugra/0.1 (career-agent)"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{HH_API_BASE}/vacancies", params=params, headers=headers)
            response.raise_for_status()
            data = response.json()

        vacancies: list[JobVacancy] = []
        for item in data.get("items", []):
            vacancies.append(
                JobVacancy(
                    id=uuid4(),
                    external_id=str(item["id"]),
                    source=self._source,
                    title=item.get("name", ""),
                    company=item.get("employer", {}).get("name", ""),
                    url=item.get("alternate_url", ""),
                    salary_from=item.get("salary", {}).get("from") if item.get("salary") else None,
                    salary_to=item.get("salary", {}).get("to") if item.get("salary") else None,
                    is_remote=filters.remote_only,
                )
            )

        logger.info("hh_search_completed", count=len(vacancies), source=self._source.value)
        return vacancies

    @async_retry()
    async def get_vacancy(self, external_id: str) -> JobVacancy | None:
        headers = {"User-Agent": "Ugra/0.1 (career-agent)"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{HH_API_BASE}/vacancies/{external_id}", headers=headers)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            item = response.json()

        salary = item.get("salary") or {}
        return JobVacancy(
            id=uuid4(),
            external_id=str(item["id"]),
            source=self._source,
            title=item.get("name", ""),
            company=item.get("employer", {}).get("name", ""),
            description=item.get("description", ""),
            url=item.get("alternate_url", ""),
            salary_from=salary.get("from"),
            salary_to=salary.get("to"),
            currency=salary.get("currency", "RUB"),
            experience_level=_map_experience(item.get("experience", {}).get("id")),
        )


def _map_experience(hh_id: str | None) -> ExperienceLevel | None:
    mapping = {
        "noExperience": ExperienceLevel.INTERN,
        "between1And3": ExperienceLevel.JUNIOR,
        "between3And6": ExperienceLevel.MIDDLE,
        "moreThan6": ExperienceLevel.SENIOR,
    }
    return mapping.get(hh_id or "")
