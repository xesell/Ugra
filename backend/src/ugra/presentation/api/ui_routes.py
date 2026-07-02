"""UI-specific REST endpoints for the web dashboard."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ugra.application.ui.event_store import get_ui_event_store
from ugra.application.ui.state import get_ui_state_store
from ugra.application.use_cases import GenerateCoverLetterUseCase, SearchJobsUseCase
from ugra.config.settings import get_settings
from ugra.core.di.container import Container
from ugra.domain.events import ApplicationSubmitted
from ugra.domain.candidate_profile import ANALYSIS_STEPS
from ugra.domain.value_objects import JobFilter

DEFAULT_UI_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


def _ui_user_id() -> UUID:
    settings = get_settings()
    if settings.default_user_id:
        return UUID(settings.default_user_id)
    return DEFAULT_UI_USER_ID


def get_container(request: Request) -> Container:
    return request.app.state.container

router = APIRouter(prefix="/ui", tags=["ui"])


class ApplyRequest(BaseModel):
    job: dict[str, Any]
    resume_title: str = ""
    cover_letter: str = ""


class ResumeRequest(BaseModel):
    id: str | None = None
    title: str
    skills: list[str] = Field(default_factory=list)
    experience_years: int = 0
    content: str = ""
    is_default: bool = False


class ProfileUpdateRequest(BaseModel):
    primary_specialization: str | None = None
    level: str | None = None
    preferred_roles: list[dict[str, str]] | None = None
    include_keywords: list[str] | None = None
    exclude_keywords: list[str] | None = None
    excluded_roles: list[str] | None = None


class CoverLetterRequest(BaseModel):
    id: str | None = None
    title: str
    content: str = ""
    suitable_for: list[str] = Field(default_factory=list)


class GenerateCoverLetterRequest(BaseModel):
    template_id: str | None = None
    job_title: str = "IT Specialist"
    company: str = "Компания"
    job_description: str = ""
    company_style: str = "formal"


class SettingsUpdate(BaseModel):
    llm_provider: str | None = None
    llm_model: str | None = None
    llm_api_key: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    search_interval_hours: int | None = None
    salary_min: int | None = None
    excluded_companies: list[str] | None = None
    keywords: list[str] | None = None
    minus_words: list[str] | None = None
    cities: list[str] | None = None
    countries: list[str] | None = None
    auto_apply: bool | None = None
    apply_after_ai_review: bool | None = None
    min_match_percent: int | None = None
    apply_delay_seconds: int | None = None
    max_applications_per_day: int | None = None
    work_hours_start: str | None = None
    work_hours_end: str | None = None
    telegram_token: str | None = None
    telegram_chat_id: str | None = None
    proxy_type: str | None = None
    proxy_host: str | None = None
    proxy_login: str | None = None
    proxy_password: str | None = None


def _system_metrics() -> dict[str, Any]:
    try:
        import psutil

        return {
            "cpu_percent": round(psutil.cpu_percent(interval=0.1), 1),
            "ram_gb": round(psutil.virtual_memory().used / (1024**3), 1),
        }
    except Exception:
        return {"cpu_percent": 0.0, "ram_gb": 0.0}


@router.get("/dashboard")
async def dashboard_stats():
    store = get_ui_event_store()
    state = get_ui_state_store()
    apps = state.list_applications()
    return {
        "stats": {
            **store.stats,
            "found": max(store.stats["found"], 0),
            "suitable": max(store.stats["suitable"], 0),
            "applied": max(store.stats["applied"], len(apps)),
            "responses": store.stats["responses"],
            "invites": store.stats["invites"],
            "errors": store.stats["errors"],
        },
        "timeline": store.get_timeline(30),
    }


@router.get("/timeline/stream")
async def timeline_stream():
    store = get_ui_event_store()
    queue = store.subscribe()

    async def event_generator():
        try:
            yield f"data: {json.dumps({'type': 'init', 'timeline': store.get_timeline(30)})}\n\n"
            while True:
                try:
                    await asyncio.wait_for(queue.get(), timeout=30.0)
                    payload = {
                        "type": "update",
                        "timeline": store.get_timeline(30),
                        "stats": store.stats,
                    }
                    yield f"data: {json.dumps(payload)}\n\n"
                except TimeoutError:
                    yield ": keepalive\n\n"
        finally:
            store.unsubscribe(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/applications")
async def list_applications():
    return {"applications": get_ui_state_store().list_applications()}


@router.get("/applications/{app_id}")
async def get_application(app_id: str):
    app = get_ui_state_store().get_application(app_id)
    if not app:
        raise HTTPException(404, "Application not found")
    from dataclasses import asdict

    return asdict(app)


@router.post("/applications/apply")
async def apply_to_job(
    request: ApplyRequest,
    container: Container = Depends(get_container),
    user_id: UUID | None = None,
):
    state = get_ui_state_store()
    store = get_ui_event_store()
    record = state.create_application(request.job, request.resume_title, request.cover_letter)

    await container.event_bus().publish(
        ApplicationSubmitted(
            job_id=UUID(request.job["id"]) if _is_uuid(request.job.get("id")) else uuid4(),
            user_id=user_id or uuid4(),
        )
    )
    store.add_timeline(request.job.get("source", "HH"), "Отправлен отклик", request.job.get("title", ""))
    return {"application": record.__dict__}


@router.post("/jobs/{job_id}/ignore")
async def ignore_job(job_id: str):
    get_ui_state_store().ignore_job(job_id)
    get_ui_event_store().add_timeline("User", "Вакансия проигнорирована", job_id)
    return {"ok": True}


@router.post("/resumes/upload")
async def upload_resume_pdf(
    file: UploadFile = File(...),
    container: Container = Depends(get_container),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported")

    data = await file.read()
    if len(data) > 10 * 1024 * 1024:
        raise HTTPException(400, "File too large (max 10 MB)")

    service = container.resume_analysis_service()
    user_id = _ui_user_id()
    job = await service.start_upload(user_id, file.filename, data)
    return {"job": job.to_status_dict(), "steps": [{"key": k, "label": l} for k, l in ANALYSIS_STEPS]}


@router.get("/resumes/analysis/{job_id}")
async def get_analysis_status(job_id: UUID, container: Container = Depends(get_container)):
    job = await container.resume_analysis_service().get_job(job_id)
    if not job:
        raise HTTPException(404, "Analysis job not found")
    result = job.to_status_dict()
    if job.profile:
        result["profile"] = job.profile.to_dict()
    return result


@router.get("/candidate-profile")
async def get_candidate_profile(container: Container = Depends(get_container)):
    profile = await container.candidate_context_provider().get_profile(_ui_user_id())
    if not profile:
        return {"profile": None}
    return {"profile": profile.to_dict()}


@router.patch("/candidate-profile")
async def update_candidate_profile(
    request: ProfileUpdateRequest,
    container: Container = Depends(get_container),
):
    service = container.candidate_profile_service()
    try:
        profile = await service.update_profile(
            _ui_user_id(),
            request.model_dump(exclude_none=True),
        )
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
    return {"profile": profile.to_dict()}


@router.get("/candidate-profile/history")
async def get_candidate_profile_history(container: Container = Depends(get_container)):
    entries = await container.candidate_profile_service().get_history(_ui_user_id())
    return {
        "history": [
            {
                "version": e.version,
                "analyzed_at": e.analyzed_at.isoformat(),
                "model": e.model,
                "duration_seconds": e.duration_seconds,
                "changes_summary": e.changes_summary,
                "trigger": e.trigger,
            }
            for e in entries
        ]
    }


@router.get("/candidate-profile/resume-preview")
async def get_resume_preview(container: Container = Depends(get_container)):
    user_id = _ui_user_id()
    profile = await container.candidate_profile_service().get_profile(user_id)
    resume_file = await container.resume_file_repository().get_latest_for_user(user_id)
    if not resume_file:
        raise HTTPException(404, "Resume file not found")
    return {
        "filename": resume_file.filename,
        "extracted_text": resume_file.extracted_text[:8000],
        "profile_specialization": profile.identity.primary_specialization if profile else "",
    }


@router.get("/candidate-profile/employer-preview")
async def get_employer_preview(container: Container = Depends(get_container)):
    """Preview of what the agent would communicate to employers."""
    profile = await container.candidate_profile_service().get_profile(_ui_user_id())
    if not profile:
        raise HTTPException(404, "Profile not found")
    resume_file = await container.resume_file_repository().get_latest_for_user(_ui_user_id())
    cover_letter = (
        f"Здравствуйте!\n\n"
        f"Меня зовут {profile.identity.full_name or 'кандидат'}. "
        f"Я {profile.identity.level.value} {profile.identity.primary_specialization} "
        f"с опытом {profile.experience_years()} лет. "
        f"Ключевые технологии: {', '.join(profile.top_skills(8))}.\n\n"
        f"С уважением,\n{profile.identity.full_name or 'Кандидат'}"
    )
    return {
        "resume_filename": resume_file.filename if resume_file else "",
        "resume_excerpt": (resume_file.extracted_text[:1500] if resume_file else ""),
        "cover_letter": cover_letter,
        "match_rationale": profile.ai_summary[:3] if profile.ai_summary else profile.strengths[:3],
    }


@router.get("/resumes")
async def list_resumes():
    return {"resumes": get_ui_state_store().list_resumes()}


@router.post("/resumes")
async def save_resume(request: ResumeRequest):
    record = get_ui_state_store().save_resume(request.model_dump())
    from dataclasses import asdict

    return asdict(record)


@router.delete("/resumes/{resume_id}")
async def delete_resume(resume_id: str):
    if not get_ui_state_store().delete_resume(resume_id):
        raise HTTPException(404, "Resume not found")
    return {"ok": True}


@router.get("/cover-letters")
async def list_cover_letters():
    return {"templates": get_ui_state_store().list_cover_letters()}


@router.post("/cover-letters")
async def save_cover_letter(request: CoverLetterRequest):
    record = get_ui_state_store().save_cover_letter(request.model_dump())
    from dataclasses import asdict

    return asdict(record)


@router.delete("/cover-letters/{letter_id}")
async def delete_cover_letter(letter_id: str):
    if not get_ui_state_store().delete_cover_letter(letter_id):
        raise HTTPException(404, "Template not found")
    return {"ok": True}


@router.post("/cover-letters/generate")
async def generate_cover_letter_ui(
    request: GenerateCoverLetterRequest,
    container: Container = Depends(get_container),
):
    profile = await container.candidate_context_provider().get_profile(_ui_user_id())
    experience = ""
    resume_content = ""
    if profile:
        experience = (
            f"{profile.identity.primary_specialization}, "
            f"{profile.experience_years()} лет опыта, уровень {profile.identity.level.value}"
        )
        resume_content = profile.prompt_context or "\n".join(profile.ai_summary or profile.strengths)

    store = get_ui_state_store()
    resumes = store.list_resumes()
    if not resumes and resume_content:
        resumes = [{"title": "Candidate Profile", "content": resume_content}]
    elif not resumes:
        resumes = [{"title": "General", "content": experience or "Опытный IT-специалист"}]

    job = {
        "id": str(uuid4()),
        "title": request.job_title,
        "company": request.company,
        "description": request.job_description,
        "technologies": profile.flat_skills()[:15] if profile else [],
    }

    use_case = GenerateCoverLetterUseCase(
        container.cover_letter_agent(),
        container.resume_agent(),
    )
    warning: str | None = None
    try:
        letter = await use_case.execute(job, resumes, experience)
    except Exception as exc:
        err = str(exc).lower()
        if "429" in err or "too many requests" in err or "rate limit" in err:
            from ugra.application.cover_letter.fallback import build_fallback_cover_letter

            template_content = ""
            if request.template_id:
                existing = next(
                    (t for t in store.list_cover_letters() if t["id"] == request.template_id),
                    None,
                )
                if existing:
                    template_content = existing.get("content", "")
            resume_content = resumes[0].get("content", "") if resumes else ""
            letter = build_fallback_cover_letter(
                job_title=request.job_title,
                company=request.company,
                job_description=request.job_description,
                experience=experience,
                resume_content=resume_content,
                template_content=template_content,
            )
            warning = (
                "OpenAI временно ограничил запросы (429). "
                "Сгенерирован черновик без AI — отредактируйте перед отправкой."
            )
        else:
            raise HTTPException(502, f"Не удалось сгенерировать письмо: {exc}") from exc

    if request.template_id:
        existing = next(
            (t for t in store.list_cover_letters() if t["id"] == request.template_id),
            None,
        )
        if existing:
            store.save_cover_letter(
                {
                    "id": request.template_id,
                    "title": existing["title"],
                    "content": letter,
                    "suitable_for": existing.get("suitable_for", []),
                }
            )

    return {"cover_letter": letter, "warning": warning}


@router.get("/sources")
async def list_sources():
    store = get_ui_event_store()
    settings = get_settings()
    last = store.last_sync.isoformat() if store.last_sync else None
    return {
        "sources": [
            {
                "id": "hh",
                "name": "HH",
                "connected": bool(settings.hh_api_token),
                "last_sync": last,
                "token_expires": None,
                "vacancies_found": store.stats["found"],
            },
            {
                "id": "geekjob",
                "name": "GeekJob",
                "connected": True,
                "last_sync": last,
                "token_expires": None,
                "vacancies_found": store.stats["found"] // 3,
            },
            {
                "id": "linkedin",
                "name": "LinkedIn",
                "connected": False,
                "last_sync": None,
                "token_expires": None,
                "vacancies_found": 0,
            },
            {
                "id": "remoteok",
                "name": "RemoteOK",
                "connected": False,
                "last_sync": None,
                "token_expires": None,
                "vacancies_found": 0,
            },
        ]
    }


@router.get("/settings")
async def get_settings_ui():
    s = get_ui_state_store().settings
    app_settings = get_settings()
    return {
        "llm_provider": s.llm_provider or app_settings.default_llm_provider,
        "llm_model": s.llm_model or app_settings.default_llm_model,
        "llm_api_key": "***" if app_settings.openai_api_key else "",
        "temperature": s.temperature,
        "max_tokens": s.max_tokens,
        "search_interval_hours": s.search_interval_hours,
        "salary_min": s.salary_min,
        "excluded_companies": s.excluded_companies,
        "keywords": s.keywords,
        "minus_words": s.minus_words,
        "cities": s.cities,
        "countries": s.countries,
        "auto_apply": s.auto_apply,
        "apply_after_ai_review": s.apply_after_ai_review,
        "min_match_percent": s.min_match_percent,
        "apply_delay_seconds": s.apply_delay_seconds,
        "max_applications_per_day": s.max_applications_per_day,
        "work_hours_start": s.work_hours_start,
        "work_hours_end": s.work_hours_end,
        "telegram_token": "***" if app_settings.telegram_bot_token else "",
        "telegram_chat_id": s.telegram_chat_id,
        "proxy_type": s.proxy_type,
        "proxy_host": s.proxy_host,
        "proxy_login": s.proxy_login,
        "proxy_password": "***" if s.proxy_password else "",
    }


@router.patch("/settings")
async def update_settings(request: SettingsUpdate):
    s = get_ui_state_store().settings
    for key, value in request.model_dump(exclude_none=True).items():
        setattr(s, key, value)
    get_ui_state_store().persist_settings()
    return await get_settings_ui()


@router.get("/logs")
async def get_logs(
    level: str | None = Query(None),
    search: str | None = Query(None),
    limit: int = Query(200, le=500),
):
    return {"logs": get_ui_event_store().get_logs(level, search, limit)}


@router.get("/status")
async def system_status(container: Container = Depends(get_container)):
    settings = get_settings()
    store = get_ui_event_store()
    mood = container.ugra_mood()
    state = container.orchestrator().state

    metrics = _system_metrics()
    last_sync = store.last_sync.strftime("%H:%M:%S") if store.last_sync else "—"

    return {
        "llm": {"provider": settings.default_llm_provider, "model": settings.default_llm_model},
        "sources": {
            "hh": "connected" if settings.hh_api_token else "disconnected",
            "geekjob": "connected",
        },
        "telegram": "online" if settings.telegram_bot_token else "offline",
        "cpu_percent": metrics["cpu_percent"],
        "ram_gb": metrics["ram_gb"],
        "last_sync": last_sync,
        "agent_mood": mood.format_status(state.agent_states.get(state.active_agent or "", "idle")),
        "active_agent": state.active_agent,
    }


@router.post("/jobs/search")
async def search_jobs_ui(
    container: Container = Depends(get_container),
    country: str | None = None,
    remote_only: bool = False,
    salary_min: int | None = None,
    technologies: list[str] = Query(default=[]),
    level: str | None = None,
    keywords: list[str] = Query(default=[]),
    skills: list[str] = Query(default=[]),
    experience_years: int = 0,
):
    user_id = _ui_user_id()
    profile = await container.candidate_context_provider().get_profile(user_id)

    skills = skills
    experience_years = experience_years
    search_keywords = list(keywords)

    if profile:
        if not skills:
            skills = profile.top_skills()
        if not experience_years:
            experience_years = profile.experience_years()
        if not search_keywords and profile.search_strategy.include_keywords:
            search_keywords = profile.search_strategy.include_keywords

    techs = technologies or (profile.flat_skills()[:10] if profile else [])
    use_case = SearchJobsUseCase(container.job_source_registry(), container.career_agent())
    job_filter = JobFilter(
        country=country,
        remote_only=remote_only,
        salary_min=salary_min,
        technologies=tuple(techs),
        level=level or (profile.identity.level.value if profile else None),
        keywords=tuple(search_keywords),
    )
    results = await use_case.execute(user_id, job_filter, skills, experience_years)
    state = get_ui_state_store()
    filtered = [j for j in results if not state.is_ignored(j.get("id", ""))]
    if profile and profile.search_strategy.exclude_keywords:
        excluded = {w.lower() for w in profile.search_strategy.exclude_keywords}
        filtered = [
            j
            for j in filtered
            if not any(w in j.get("title", "").lower() for w in excluded)
        ]
    suitable = sum(1 for j in filtered if j.get("match_score", 0) >= 70)
    get_ui_event_store().record_search(len(filtered), suitable)
    return {"jobs": filtered, "count": len(filtered)}


def _is_uuid(value: Any) -> bool:
    try:
        UUID(str(value))
        return True
    except (ValueError, TypeError):
        return False
