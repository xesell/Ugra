"""Autonomous task scheduler — agents work without user interaction."""

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from ugra.agents.base.registry import AgentContext
from ugra.agents.orchestrator.intelligence_orchestrator import IntelligenceOrchestrator
from ugra.core.events.bus import EventBus
from ugra.core.logging.setup import get_logger
from ugra.domain.events import NotificationSent, VacancyFound

logger = get_logger(__name__)

AutonomousTask = Callable[[UUID], Awaitable[None]]


@dataclass
class ScheduledTask:
    name: str
    interval_seconds: int
    handler: AutonomousTask
    last_run: datetime | None = None
    enabled: bool = True


class AutonomousScheduler:
    """Runs background tasks after application startup."""

    DEFAULT_TASKS = [
        "search_vacancies",
        "analyze_new_vacancies",
        "study_market_requirements",
        "update_statistics",
        "check_new_messages",
    ]

    def __init__(
        self,
        orchestrator: IntelligenceOrchestrator,
        event_bus: EventBus,
        default_user_id: UUID | None = None,
        interval_seconds: int = 300,
    ):
        self._orchestrator = orchestrator
        self._events = event_bus
        self._default_user_id = default_user_id
        self._interval = interval_seconds
        self._tasks: list[ScheduledTask] = []
        self._running = False
        self._task_handle: asyncio.Task | None = None

    def register(self, name: str, handler: AutonomousTask, interval_seconds: int | None = None) -> None:
        self._tasks.append(
            ScheduledTask(
                name=name,
                interval_seconds=interval_seconds or self._interval,
                handler=handler,
            )
        )

    def _register_defaults(self, user_id: UUID) -> None:
        self.register("search_vacancies", lambda uid: self._search_vacancies(uid))
        self.register("analyze_new_vacancies", lambda uid: self._analyze_vacancies(uid))
        self.register("study_market_requirements", lambda uid: self._study_market(uid))
        self.register("update_statistics", lambda uid: self._update_stats(uid))
        self.register("check_new_messages", lambda uid: self._check_messages(uid))

    async def start(self, user_id: UUID | None = None) -> None:
        uid = user_id or self._default_user_id
        if not uid:
            logger.warning("autonomous_scheduler_no_user")
            return

        if not self._tasks:
            self._register_defaults(uid)

        self._running = True
        self._task_handle = asyncio.create_task(self._run_loop(uid))
        logger.info("autonomous_scheduler_started", user_id=str(uid), tasks=len(self._tasks))

    async def stop(self) -> None:
        self._running = False
        if self._task_handle:
            self._task_handle.cancel()
            try:
                await self._task_handle
            except asyncio.CancelledError:
                pass
        logger.info("autonomous_scheduler_stopped")

    async def _run_loop(self, user_id: UUID) -> None:
        while self._running:
            for task in self._tasks:
                if not task.enabled:
                    continue
                try:
                    logger.info("autonomous_task_start", task=task.name)
                    await task.handler(user_id)
                    task.last_run = datetime.utcnow()
                except Exception:
                    logger.exception("autonomous_task_failed", task=task.name)
            await asyncio.sleep(self._interval)

    async def _search_vacancies(self, user_id: UUID) -> None:
        results = await self._orchestrator.plan_and_execute(user_id)
        for result in results:
            for job in result.data.get("jobs", []):
                await self._events.publish(
                    VacancyFound(
                        job_id=UUID(job["id"]) if isinstance(job.get("id"), str) else job.get("id"),
                        user_id=user_id,
                        title=job.get("title", ""),
                        company=job.get("company", ""),
                    )
                )

    async def _analyze_vacancies(self, user_id: UUID) -> None:
        await self._orchestrator.invoke_agent(
            "career_agent",
            AgentContext(
                user_id=user_id,
                message="analyze new vacancies",
                metadata={"autonomous": True},
            ),
        )

    async def _study_market(self, user_id: UUID) -> None:
        await self._orchestrator.invoke_agent(
            "learning_agent",
            AgentContext(
                user_id=user_id,
                message="study market requirements",
                metadata={"autonomous": True},
            ),
        )

    async def _update_stats(self, user_id: UUID) -> None:
        logger.info("stats_updated", user_id=str(user_id))

    async def _check_messages(self, user_id: UUID) -> None:
        await self._events.publish(
            NotificationSent(user_id=user_id, channel="internal", message="Message check completed")
        )
