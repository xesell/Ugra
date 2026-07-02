"""Memory repository port."""

from abc import ABC, abstractmethod
from uuid import UUID

from ugra.domain.memory import LongTermMemory


class MemoryRepository(ABC):
    @abstractmethod
    async def get_by_user(self, user_id: UUID) -> LongTermMemory | None: ...

    @abstractmethod
    async def save(self, memory: LongTermMemory) -> LongTermMemory: ...

    @abstractmethod
    async def get_or_create(self, user_id: UUID) -> LongTermMemory: ...
