"""In-process event bus."""

from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any

from ugra.core.logging.setup import get_logger
from ugra.domain.events import DomainEvent

logger = get_logger(__name__)

EventHandler = Callable[[DomainEvent], Awaitable[None]]


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[type[DomainEvent], list[EventHandler]] = defaultdict(list)

    def subscribe(self, event_type: type[DomainEvent], handler: EventHandler) -> None:
        self._handlers[event_type].append(handler)

    async def publish(self, event: DomainEvent) -> None:
        handlers = self._handlers.get(type(event), [])
        for handler in handlers:
            try:
                await handler(event)
            except Exception:
                logger.exception(
                    "event_handler_failed",
                    event_type=type(event).__name__,
                    event_id=str(event.event_id),
                )

    async def publish_all(self, events: list[DomainEvent]) -> None:
        for event in events:
            await self.publish(event)
