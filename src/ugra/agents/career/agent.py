"""Career Agent — LangGraph workflow with Intelligence Core integration."""

from typing import TypedDict
from uuid import UUID

from langgraph.graph import END, StateGraph

from ugra.agents.base.registry import AgentCapability, AgentResponse
from ugra.application.intelligence.cognition_engine import CognitionEngine
from ugra.application.intelligence.goal_manager import GoalManager
from ugra.agents.runtime.memory import AgentMemory
from ugra.application.intelligence.personality_service import PersonalityService
from ugra.core.events.bus import EventBus
from ugra.core.intelligence.agent_runtime import AgentRuntimeContext, IntelligenceAgent
from ugra.core.logging.setup import get_logger
from ugra.core.tools.base import ToolRegistry
from ugra.domain.agent_state import AgentState
from ugra.domain.entities import JobVacancy
from ugra.domain.events import SkillGapDetected, VacancyFound
from ugra.domain.repositories.memory import MemoryRepository
from ugra.domain.value_objects import JobFilter, MatchScore
from ugra.infrastructure.adapters.job_sources.registry import JobSourceRegistry
from ugra.infrastructure.llm.service import LLMService
from ugra.infrastructure.prompts.manager import PromptManager
from ugra.infrastructure.rag.knowledge_base import KnowledgeBase

logger = get_logger(__name__)


class CareerState(TypedDict):
    message: str
    user_skills: list[str]
    user_experience: int
    jobs: list[dict]
    analyzed_jobs: list[dict]
    response: str


class CareerAgent(IntelligenceAgent):
    """Career Agent — job search, analysis, match scoring with full intelligence core."""

    def __init__(
        self,
        *,
        personality: PersonalityService,
        cognition: CognitionEngine,
        goal_manager: GoalManager,
        memory_repo: MemoryRepository,
        agent_memory: AgentMemory,
        tool_registry: ToolRegistry,
        prompt_manager: PromptManager,
        event_bus: EventBus,
        llm: LLMService,
        job_sources: JobSourceRegistry,
        knowledge_base: KnowledgeBase | None = None,
    ):
        super().__init__(
            personality=personality,
            cognition=cognition,
            goal_manager=goal_manager,
            memory_repo=memory_repo,
            tool_registry=tool_registry,
            prompt_manager=prompt_manager,
            event_bus=event_bus,
        )
        self._llm = llm
        self._job_sources = job_sources
        self._agent_memory = agent_memory
        self._kb = knowledge_base
        self._graph = self._build_graph()

    @property
    def name(self) -> str:
        return "career_agent"

    @property
    def capabilities(self) -> list[AgentCapability]:
        return [
            AgentCapability.JOB_SEARCH,
            AgentCapability.JOB_ANALYSIS,
            AgentCapability.SKILL_GAP,
        ]

    @property
    def graph(self):
        return self._graph

    async def can_handle(self, context) -> float:
        keywords = ["job", "vacancy", "work", "ваканс", "работ", "jobs", "/jobs", "/top"]
        msg = context.message.lower()
        if any(k in msg for k in keywords):
            return 0.9
        return 0.1

    async def execute(self, ctx: AgentRuntimeContext) -> AgentResponse:
        user_skills = ctx.metadata.get("skills", [])
        user_experience = ctx.metadata.get("experience_years", 0)
        filters = ctx.metadata.get("filters", {})

        await self._set_state(AgentState.SEARCHING, ctx.user_id)

        if "search" in ctx.message.lower() or "/jobs" in ctx.message:
            job_filter = JobFilter(
                keywords=tuple(filters.get("keywords", [])),
                remote_only=filters.get("remote_only", False),
                salary_min=filters.get("salary_min"),
                country=filters.get("country"),
                technologies=tuple(filters.get("technologies", [])),
                level=filters.get("level"),
            )
            jobs = await self._job_sources.search_all(job_filter)
            analyzed = [
                await self._analyze_job(job, user_skills, user_experience, ctx.user_id)
                for job in jobs[:10]
            ]

            memory = await self.load_memory(ctx.user_id)
            for job_data in analyzed:
                should_apply, _ = self._cognition.evaluate_vacancy_fit(
                    ctx.user_id, job_data, memory, await self._goals.get_active_goal(ctx.user_id)
                )
                job_data["recommended"] = should_apply
                await self._agent_memory.record_vacancy(
                    ctx.user_id,
                    UUID(job_data["id"]),
                    job_data["title"],
                    job_data["company"],
                    job_data["match_score"],
                )
                await self._events.publish(
                    VacancyFound(
                        job_id=UUID(job_data["id"]),
                        user_id=ctx.user_id,
                        title=job_data["title"],
                        company=job_data["company"],
                        match_score=job_data["match_score"],
                    )
                )

            return AgentResponse(
                agent_name=self.name,
                content=self._format_jobs_response(analyzed),
                data={"jobs": analyzed},
                capabilities_used=[AgentCapability.JOB_SEARCH, AgentCapability.JOB_ANALYSIS],
            )

        await self._set_state(AgentState.WRITING, ctx.user_id)
        system_prompt = await self.get_system_prompt(ctx.user_id)
        response_text = await self._llm.generate(system_prompt, ctx.message)

        return AgentResponse(
            agent_name=self.name,
            content=response_text,
            capabilities_used=self.capabilities,
        )

    def _build_graph(self) -> StateGraph:
        graph = StateGraph(CareerState)
        graph.add_node("analyze_intent", self._analyze_intent)
        graph.add_node("respond", self._respond)
        graph.set_entry_point("analyze_intent")
        graph.add_edge("analyze_intent", "respond")
        graph.add_edge("respond", END)
        return graph.compile()

    async def _analyze_intent(self, state: CareerState) -> dict:
        return {"response": f"Processing: {state['message']}"}

    async def _respond(self, state: CareerState) -> dict:
        return state

    async def _analyze_job(
        self, job: JobVacancy, user_skills: list[str], experience_years: int, user_id: UUID
    ) -> dict:
        await self._set_state(AgentState.THINKING, user_id)
        system_prompt = await self.get_system_prompt(user_id)

        rag_context = ""
        if self._kb:
            chunks = await self._kb.search(f"{job.title} {job.description[:500]}")
            rag_context = "\n".join(c.content[:200] for c in chunks[:3])

        schema = {
            "match_score": "float 0-100",
            "required_skills": ["list of strings"],
            "preferred_skills": ["list of strings"],
            "technologies": ["list of strings"],
            "experience_level": "string",
            "requires_english": "boolean",
            "requires_relocation": "boolean",
            "pros": ["matching user skills"],
            "cons": ["missing user skills"],
            "skill_gaps": ["skills user lacks"],
        }

        prompt = f"""Analyze this job vacancy:

Title: {job.title}
Company: {job.company}
Description: {job.description[:2000]}

User skills: {', '.join(user_skills)}
User experience: {experience_years} years

Knowledge context: {rag_context}
"""

        try:
            analysis = await self._llm.generate_structured(system_prompt, prompt, schema)
        except Exception:
            logger.exception("job_analysis_failed", job_id=str(job.id))
            analysis = self._fallback_analysis(job, user_skills)

        match = MatchScore(
            value=float(analysis.get("match_score", 50)),
            pros=tuple(analysis.get("pros", [])),
            cons=tuple(analysis.get("cons", [])),
        )

        if analysis.get("skill_gaps"):
            await self._events.publish(
                SkillGapDetected(
                    user_id=user_id,
                    job_id=job.id,
                    missing_skills=tuple(analysis.get("skill_gaps", [])),
                )
            )

        return {
            "id": str(job.id),
            "title": job.title,
            "company": job.company,
            "url": job.url,
            "source": job.source.value,
            "match_score": match.value,
            "match_percentage": match.percentage,
            "pros": list(match.pros),
            "cons": list(match.cons),
            "skill_gaps": analysis.get("skill_gaps", []),
            "technologies": analysis.get("technologies", []),
            "experience_level": analysis.get("experience_level"),
            "requires_english": analysis.get("requires_english", False),
            "requires_relocation": analysis.get("requires_relocation", False),
        }

    def _fallback_analysis(self, job: JobVacancy, user_skills: list[str]) -> dict:
        job_tech = set(t.lower() for t in job.technologies)
        user_set = set(s.lower() for s in user_skills)
        matched = job_tech & user_set
        missing = job_tech - user_set
        score = (len(matched) / max(len(job_tech), 1)) * 100

        return {
            "match_score": score,
            "pros": list(matched),
            "cons": list(missing),
            "skill_gaps": list(missing),
            "technologies": list(job_tech),
            "experience_level": job.experience_level.value if job.experience_level else "unknown",
            "requires_english": False,
            "requires_relocation": job.requires_relocation,
        }

    def _format_jobs_response(self, jobs: list[dict]) -> str:
        if not jobs:
            return "Вакансии не найдены. Попробуйте изменить фильтры."

        lines = ["📋 *Найденные вакансии:*\n"]
        for job in sorted(jobs, key=lambda j: j["match_score"], reverse=True):
            pros = " ".join(f"✔ {p}" for p in job["pros"][:3])
            cons = " ".join(f"✖ {c}" for c in job["cons"][:3])
            gaps = "\n".join(f"• {g}" for g in job.get("skill_gaps", [])[:3])

            lines.append(
                f"*{job['title']}* — {job['company']}\n"
                f"Match Score: *{job['match_percentage']}*\n"
                f"{pros}\n{cons}\n"
                f"{'Недостаёт:\n' + gaps if gaps else ''}"
                f"[Открыть]({job['url']})\n"
            )
        return "\n".join(lines)

    async def analyze_single(self, job: JobVacancy, user_id: UUID, skills: list[str], exp: int) -> dict:
        return await self._analyze_job(job, skills, exp, user_id)
