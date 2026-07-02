"""Memory repository factory — PostgreSQL with in-memory fallback."""

from sqlalchemy.ext.asyncio import async_sessionmaker

from ugra.config.settings import Settings
from ugra.domain.repositories.memory import MemoryRepository
from ugra.infrastructure.persistence.repositories.memory_repository import (
    InMemoryMemoryRepository,
    PostgresMemoryRepository,
)


def create_memory_repository(
    settings: Settings,
    session_factory: async_sessionmaker | None = None,
) -> MemoryRepository:
    if settings.use_postgres_memory and session_factory is not None:
        return PostgresMemoryRepository(session_factory)
    return InMemoryMemoryRepository()
