"""Job source registry — add new sources without modifying existing code."""

from ugra.domain.value_objects import JobFilter
from ugra.infrastructure.adapters.job_sources.base import JobSourceAdapter


class JobSourceRegistry:
    def __init__(self) -> None:
        self._adapters: dict[str, JobSourceAdapter] = {}

    def register(self, adapter: JobSourceAdapter) -> None:
        self._adapters[adapter.source_name] = adapter

    def get(self, source_name: str) -> JobSourceAdapter | None:
        return self._adapters.get(source_name)

    @property
    def sources(self) -> list[str]:
        return list(self._adapters.keys())

    async def search_all(self, filters: JobFilter) -> list:
        from ugra.domain.entities import JobVacancy

        results: list[JobVacancy] = []
        sources = filters.sources if filters.sources else self.sources

        for name in sources:
            adapter = self._adapters.get(name)
            if adapter:
                results.extend(await adapter.search(filters))

        return results
