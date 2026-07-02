"""Application use cases."""

from uuid import UUID

from ugra.agents.career.agent import CareerAgent
from ugra.agents.cover_letter.agent import CoverLetterAgent
from ugra.agents.interview.agent import InterviewAgent
from ugra.agents.orchestrator.intelligence_orchestrator import IntelligenceOrchestrator
from ugra.agents.resume.agent import ResumeAgent
from ugra.core.events.bus import EventBus
from ugra.domain.events import JobAnalyzed, SkillGapDetected
from ugra.domain.value_objects import JobFilter
from ugra.infrastructure.adapters.job_sources.registry import JobSourceRegistry


class SearchJobsUseCase:
    def __init__(self, job_sources: JobSourceRegistry, career_agent: CareerAgent):
        self._sources = job_sources
        self._career = career_agent

    async def execute(self, user_id: UUID, filters: JobFilter, skills: list[str], exp: int) -> list[dict]:
        jobs = await self._sources.search_all(filters)
        return [await self._career.analyze_single(job, user_id, skills, exp) for job in jobs[:20]]


class AnalyzeJobUseCase:
    def __init__(self, career_agent: CareerAgent, event_bus: EventBus):
        self._career = career_agent
        self._events = event_bus

    async def execute(self, job_data: dict, user_id: UUID, skills: list[str], exp: int) -> dict:
        from ugra.domain.entities import JobVacancy

        job = JobVacancy(**{k: v for k, v in job_data.items() if k in JobVacancy.__dataclass_fields__})
        result = await self._career.analyze_single(job, user_id, skills, exp)

        await self._events.publish(
            JobAnalyzed(job_id=job.id, user_id=user_id, match_score=result["match_score"])
        )
        if result.get("skill_gaps"):
            await self._events.publish(
                SkillGapDetected(
                    user_id=user_id,
                    job_id=job.id,
                    missing_skills=tuple(result["skill_gaps"]),
                )
            )
        return result


class GenerateCoverLetterUseCase:
    def __init__(self, cover_letter_agent: CoverLetterAgent, resume_agent: ResumeAgent):
        self._cover_letter = cover_letter_agent
        self._resume = resume_agent

    async def execute(self, job: dict, resumes: list[dict], experience: str = "") -> str:
        best = await self._resume.select_best(resumes, job)  # type: ignore[arg-type]
        if not best:
            return "No resume available."
        return await self._cover_letter.generate(job=job, resume_content=best["content"], user_experience=experience)


class PrepareInterviewUseCase:
    def __init__(self, interview_agent: InterviewAgent):
        self._interview = interview_agent

    async def execute(self, job: dict, skills: list[str]) -> dict:
        prep = await self._interview.prepare(job, skills)
        return {
            "questions": prep.questions,
            "answers": prep.answers,
            "topics": prep.topics,
            "checklist": prep.checklist,
        }


class RouteMessageUseCase:
    def __init__(self, orchestrator: IntelligenceOrchestrator):
        self._orchestrator = orchestrator

    async def execute(self, user_id: UUID, message: str, metadata: dict | None = None):
        from ugra.agents.base.registry import AgentContext

        context = AgentContext(user_id=user_id, message=message, metadata=metadata or {})
        return await self._orchestrator.route(context)
