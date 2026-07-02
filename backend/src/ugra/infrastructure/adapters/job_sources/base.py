"""Job source adapter interface."""

from abc import ABC, abstractmethod

from ugra.domain.entities import JobVacancy
from ugra.domain.value_objects import JobFilter


class JobSourceAdapter(ABC):
    @property
    @abstractmethod
    def source_name(self) -> str: ...

    @abstractmethod
    async def search(self, filters: JobFilter) -> list[JobVacancy]: ...

    @abstractmethod
    async def get_vacancy(self, external_id: str) -> JobVacancy | None: ...
