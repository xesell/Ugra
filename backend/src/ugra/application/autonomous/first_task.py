"""First autonomous task — runs once on startup without user interaction.

Pipeline: search vacancies → analyze → save to memory → notify owner.
"""

from uuid import UUID

from ugra.agents.base.registry import AgentContext
from ugra.agents.orchestrator.intelligence_orchestrator import IntelligenceOrchestrator
from ugra.agents.runtime.memory import AgentMemory
from ugra.application.intelligence.ugra_mood import UgraMoodService
from ugra.core.events.bus import EventBus
from ugra.core.logging.setup import get_logger
from ugra.domain.agent_state import AgentState
from ugra.domain.events import NotificationSent, VacancyFound

logger = get_logger(__name__)


class FirstAutonomousTask:
    """Ugra's first action after app starts — no user required."""

    def __init__(
        self,
        orchestrator: IntelligenceOrchestrator,
        memory: AgentMemory,
        mood: UgraMoodService,
        event_bus: EventBus,
    ):
        self._orchestrator = orchestrator
        self._memory = memory
        self._mood = mood
        self._events = event_bus
        self._completed = False

    @property
    def completed(self) -> bool:
        return self._completed

    async def run(self, user_id: UUID) -> dict:
        logger.info("first_autonomous_task_start", user_id=str(user_id))
        status = self._mood.format_status(AgentState.SEARCHING)
        results: dict = {"status": status, "vacancies_found": 0, "vacancies_saved": 0}

        await self._orchestrator.start_agent("career_agent", user_id)

        # 1. Search vacancies
        search_result = await self._orchestrator.invoke_agent(
            "career_agent",
            AgentContext(
                user_id=user_id,
                message="/jobs search",
                metadata={"autonomous": True, "is_owner": True, "channel": "owner"},
            ),
        )

        jobs = search_result.data.get("jobs", [])
        results["vacancies_found"] = len(jobs)

        # 2. Analyze & 3. Save to memory
        for job in jobs[:5]:
            job_id = job.get("id")
            if not job_id:
                continue
            from uuid import UUID as ParseUUID

            parsed_id = ParseUUID(job_id) if isinstance(job_id, str) else job_id
            await self._memory.record_vacancy(
                user_id=user_id,
                job_id=parsed_id,
                title=job.get("title", ""),
                company=job.get("company", ""),
                match_score=job.get("match_score", 0.0),
            )
            results["vacancies_saved"] += 1

            await self._events.publish(
                VacancyFound(
                    job_id=parsed_id,
                    user_id=user_id,
                    title=job.get("title", ""),
                    company=job.get("company", ""),
                    match_score=job.get("match_score", 0.0),
                )
            )

        # 4. Notify owner
        top = jobs[0] if jobs else None
        if top:
            message = (
                f"Пока тебя не было, я нашла {len(jobs)} вакансий. "
                f"Лучшая: {top.get('title')} в {top.get('company')} "
                f"(Match {top.get('match_percentage', '?')})."
            )
        else:
            message = "Пока тебя не было, я проверила рынок — новых подходящих вакансий пока нет."

        await self._events.publish(
            NotificationSent(user_id=user_id, channel="telegram", message=message)
        )
        results["notification"] = message
        results["final_status"] = self._mood.format_status(AgentState.WAITING)

        self._completed = True
        logger.info("first_autonomous_task_complete", **{k: v for k, v in results.items() if k != "notification"})
        return results
