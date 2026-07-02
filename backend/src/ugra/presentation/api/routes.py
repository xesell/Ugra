"""REST API routes."""

from uuid import UUID, uuid4

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ugra.application.use_cases import (
    AnalyzeJobUseCase,
    GenerateCoverLetterUseCase,
    PrepareInterviewUseCase,
    RouteMessageUseCase,
    SearchJobsUseCase,
)
from ugra.core.di.container import Container
from ugra.domain.goals import GoalType
from ugra.domain.value_objects import JobFilter

router = APIRouter()


class JobFilterRequest(BaseModel):
    country: str | None = None
    remote_only: bool = False
    salary_min: int | None = None
    technologies: list[str] = Field(default_factory=list)
    level: str | None = None
    keywords: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)


class MessageRequest(BaseModel):
    user_id: UUID | None = None
    message: str
    metadata: dict = Field(default_factory=dict)


class HealthResponse(BaseModel):
    status: str
    version: str


@router.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok", version="0.1.0")


@router.get("/agents")
@inject
async def list_agents(container: Container = Depends(Provide[Container])):
    registry = container.agent_registry()
    return [
        {"name": a.name, "capabilities": [c.value for c in a.capabilities]}
        for a in registry.agents
    ]


@router.post("/jobs/search")
async def search_jobs(
    filters: JobFilterRequest,
    skills: list[str] = [],
    experience_years: int = 0,
):
    container = Container()
    use_case = SearchJobsUseCase(container.job_source_registry(), container.career_agent())
    job_filter = JobFilter(
        country=filters.country,
        remote_only=filters.remote_only,
        salary_min=filters.salary_min,
        technologies=tuple(filters.technologies),
        level=filters.level,
        keywords=tuple(filters.keywords),
        sources=tuple(filters.sources),
    )
    results = await use_case.execute(uuid4(), job_filter, skills, experience_years)
    return {"jobs": results, "count": len(results)}


@router.post("/message")
@inject
async def route_message(
    request: MessageRequest,
    orchestrator=Depends(Provide[Container.orchestrator]),
):
    use_case = RouteMessageUseCase(orchestrator)
    user_id = request.user_id or uuid4()
    response = await use_case.execute(user_id, request.message, request.metadata)
    return {
        "agent": response.agent_name,
        "content": response.content,
        "data": response.data,
    }


@router.post("/jobs/{job_id}/cover-letter")
async def generate_cover_letter(job: dict, resumes: list[dict], experience: str = ""):
    container = Container()
    use_case = GenerateCoverLetterUseCase(container.cover_letter_agent(), container.resume_agent())
    letter = await use_case.execute(job, resumes, experience)
    return {"cover_letter": letter}


@router.post("/jobs/{job_id}/interview-prep")
async def interview_prep(job: dict, skills: list[str] = []):
    container = Container()
    use_case = PrepareInterviewUseCase(container.interview_agent())
    return await use_case.execute(job, skills)


class GoalRequest(BaseModel):
    user_id: UUID
    title: str
    goal_type: str = "custom"
    description: str = ""


@router.post("/goals")
@inject
async def set_goal(
    request: GoalRequest,
    goal_manager=Depends(Provide[Container.goal_manager]),
):
    goal = await goal_manager.set_goal(
        request.user_id,
        request.title,
        GoalType(request.goal_type),
        request.description,
    )
    return {"id": str(goal.id), "title": goal.title, "status": goal.status.value}


@router.get("/goals/{user_id}")
@inject
async def get_goals(user_id: UUID, goal_manager=Depends(Provide[Container.goal_manager])):
    goals = await goal_manager._repo.get_by_user(user_id)
    return [{"id": str(g.id), "title": g.title, "status": g.status.value, "progress": g.progress} for g in goals]


@router.get("/agents/state")
@inject
async def agent_states(
    orchestrator=Depends(Provide[Container.orchestrator]),
    mood=Depends(Provide[Container.ugra_mood]),
):
    state = orchestrator.state
    return {
        "active_agent": state.active_agent,
        "agents": state.agent_states,
        "mood_labels": mood.format_all(state.agent_states),
    }


@router.get("/agents/mood")
@inject
async def agent_mood(
    orchestrator=Depends(Provide[Container.orchestrator]),
    mood=Depends(Provide[Container.ugra_mood]),
):
    state = orchestrator.state
    active = state.active_agent
    active_state = state.agent_states.get(active, "idle") if active else "idle"
    return {
        "status": mood.format_status(active_state),
        "agent": active,
        "all": mood.format_all(state.agent_states),
    }


@router.get("/reasoning/{user_id}")
@inject
async def get_reasoning(
    user_id: UUID,
    limit: int = 20,
    cognition=Depends(Provide[Container.cognition_engine]),
):
    records = cognition.get_reasoning(user_id, limit)
    return [
        {
            "agent": r.agent_name,
            "category": r.category.value,
            "decision": r.decision,
            "rationale": r.rationale,
            "confidence": r.confidence,
        }
        for r in records
    ]


@router.get("/memory/{user_id}")
@inject
async def get_memory(user_id: UUID, memory_repo=Depends(Provide[Container.memory_repository])):
    memory = await memory_repo.get_or_create(user_id)
    return {
        "user_id": str(memory.user_id),
        "vacancies": len(memory.vacancy_history),
        "interviews": len(memory.interview_history),
        "offers": len(memory.offer_history),
        "ignored_companies": [c.company for c in memory.ignored_companies],
        "learned_technologies": [t.name for t in memory.learned_technologies],
    }
