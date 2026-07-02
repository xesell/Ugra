"""In-memory event store for UI timeline and logs."""

from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from ugra.core.events.bus import EventBus
from ugra.domain.events import (
    AgentStateChanged,
    ApplicationSubmitted,
    DomainEvent,
    GoalProgressUpdated,
    InterviewReceived,
    InterviewScheduled,
    JobAnalyzed,
    LearningCompleted,
    NotificationSent,
    OfferReceived,
    ResumeUpdated,
    SkillGapDetected,
    VacancyFound,
)


@dataclass
class TimelineEntry:
    id: str
    time: str
    source: str
    title: str
    detail: str = ""
    event_type: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class LogEntry:
    id: str
    time: str
    level: str
    service: str
    message: str


class UIEventStore:
    def __init__(self, max_timeline: int = 500, max_logs: int = 1000) -> None:
        self._timeline: deque[TimelineEntry] = deque(maxlen=max_timeline)
        self._logs: deque[LogEntry] = deque(maxlen=max_logs)
        self._subscribers: list[Any] = []
        self.stats = {
            "found": 0,
            "suitable": 0,
            "applied": 0,
            "responses": 0,
            "invites": 0,
            "errors": 0,
        }
        self.last_sync: datetime | None = None

    def _now(self) -> str:
        return datetime.now(timezone.utc).strftime("%H:%M")

    def _log(self, level: str, service: str, message: str) -> None:
        entry = LogEntry(
            id=str(uuid4()),
            time=datetime.now(timezone.utc).isoformat(),
            level=level,
            service=service,
            message=message,
        )
        self._logs.appendleft(entry)
        self._notify()

    def add_timeline(self, source: str, title: str, detail: str = "", event_type: str = "") -> TimelineEntry:
        entry = TimelineEntry(
            id=str(uuid4()),
            time=self._now(),
            source=source,
            title=title,
            detail=detail,
            event_type=event_type,
        )
        self._timeline.appendleft(entry)
        self._notify()
        return entry

    def _notify(self) -> None:
        for queue in list(self._subscribers):
            try:
                queue.put_nowait("update")
            except Exception:
                pass

    def subscribe(self) -> Any:
        import asyncio

        queue: asyncio.Queue[str] = asyncio.Queue()
        self._subscribers.append(queue)
        return queue

    def unsubscribe(self, queue: Any) -> None:
        if queue in self._subscribers:
            self._subscribers.remove(queue)

    def get_timeline(self, limit: int = 50) -> list[dict[str, Any]]:
        return [asdict(e) for e in list(self._timeline)[:limit]]

    def get_logs(
        self,
        level: str | None = None,
        search: str | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        items = list(self._logs)
        if level:
            items = [i for i in items if i.level.upper() == level.upper()]
        if search:
            q = search.lower()
            items = [i for i in items if q in i.message.lower() or q in i.service.lower()]
        return [asdict(i) for i in items[:limit]]

    def record_search(self, count: int, suitable: int) -> None:
        self.stats["found"] += count
        self.stats["suitable"] += suitable
        self.last_sync = datetime.now(timezone.utc)
        self.add_timeline("Agent", "Поиск завершён", f"Найдено {count}, подходящих {suitable}", "search")
        self._log("INFO", "job_search", f"Search completed: {count} jobs, {suitable} suitable")

    def _handle_domain_event(self, event: DomainEvent) -> None:
        name = type(event).__name__

        if isinstance(event, VacancyFound):
            self.stats["found"] += 1
            if event.match_score >= 70:
                self.stats["suitable"] += 1
            self.add_timeline(
                "HH",
                "Найдена новая вакансия",
                f"{event.title} — {event.company}",
                name,
            )
            self._log("INFO", "vacancy", f"Found: {event.title} at {event.company}")

        elif isinstance(event, JobAnalyzed):
            self.add_timeline(
                "GPT",
                "Оценка соответствия",
                f"{event.match_score:.0f}%",
                name,
            )

        elif isinstance(event, ApplicationSubmitted):
            self.stats["applied"] += 1
            self.add_timeline("HH", "Отправлен отклик", str(event.job_id), name)
            self._log("INFO", "application", f"Application submitted for job {event.job_id}")

        elif isinstance(event, InterviewReceived | InterviewScheduled):
            self.stats["invites"] += 1
            self.stats["responses"] += 1
            self.add_timeline("HR", "Приглашение на интервью", str(event.job_id), name)

        elif isinstance(event, OfferReceived):
            self.stats["responses"] += 1
            self.add_timeline("HR", "Получено предложение", str(event.salary or ""), name)

        elif isinstance(event, SkillGapDetected):
            skills = ", ".join(event.missing_skills[:3])
            self.add_timeline("GPT", "Обнаружен skill gap", skills, name)

        elif isinstance(event, AgentStateChanged):
            self.add_timeline(
                event.agent_name or "Agent",
                f"Состояние: {event.new_state}",
                f"{event.previous_state} → {event.new_state}",
                name,
            )
            if event.new_state == "error":
                self.stats["errors"] += 1
                self._log("ERROR", event.agent_name, f"Agent error state")

        elif isinstance(event, NotificationSent):
            self._log("INFO", event.channel, event.message[:200])

        elif isinstance(event, ResumeUpdated):
            self.add_timeline("Resume", "Резюме обновлено", f"v{event.version}", name)

        elif isinstance(event, LearningCompleted):
            self.add_timeline("Learning", "Обучение завершено", event.skill, name)

        elif isinstance(event, GoalProgressUpdated):
            self.add_timeline("Goals", "Прогресс цели", f"{event.progress:.0f}%", name)

        else:
            self._log("DEBUG", "events", name)


def wire_event_store(event_bus: EventBus, store: UIEventStore) -> None:
    event_types: list[type[DomainEvent]] = [
        VacancyFound,
        JobAnalyzed,
        ApplicationSubmitted,
        InterviewReceived,
        InterviewScheduled,
        OfferReceived,
        ResumeUpdated,
        SkillGapDetected,
        LearningCompleted,
        NotificationSent,
        AgentStateChanged,
        GoalProgressUpdated,
    ]

    async def handler(event: DomainEvent) -> None:
        store._handle_domain_event(event)

    for event_type in event_types:
        event_bus.subscribe(event_type, handler)


_ui_event_store: UIEventStore | None = None


def get_ui_event_store() -> UIEventStore:
    global _ui_event_store
    if _ui_event_store is None:
        _ui_event_store = UIEventStore()
    return _ui_event_store
