"""AI resume analysis pipeline — builds internal candidate profile."""

from __future__ import annotations

import asyncio
import time
from typing import Any
from uuid import UUID

from ugra.application.candidate.prompt_context import build_prompt_context
from ugra.application.resume.fallback_analysis import build_fallback_analysis, is_rate_limit_error
from ugra.core.events.bus import EventBus
from ugra.core.logging.setup import get_logger
from ugra.domain.candidate_profile import (
    ANALYSIS_STEPS,
    AnalysisJob,
    AnalysisMeta,
    AnalysisStats,
    AnalysisStatus,
    CandidateIdentity,
    CandidateProfile,
    ExperienceBreakdown,
    ResumeFile,
    RolePriority,
    SearchStrategy,
    SpecialistLevel,
    TechSkill,
)
from ugra.domain.events import ResumeUpdated
from ugra.domain.repositories.candidate_profile import (
    AnalysisJobStore,
    CandidateProfileRepository,
    ResumeFileRepository,
)
from ugra.infrastructure.llm.service import LLMService
from ugra.infrastructure.resume.pdf_extractor import extract_text_from_pdf
from ugra.infrastructure.resume.file_storage import ResumeFileStorage
from ugra.config.settings import Settings, get_settings

logger = get_logger(__name__)

ANALYSIS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "full_name": {"type": "string"},
        "primary_specialization": {"type": "string"},
        "secondary_specializations": {"type": "array", "items": {"type": "string"}},
        "level": {"type": "string", "enum": ["junior", "middle", "senior", "lead", "architect"]},
        "level_rationale": {"type": "string"},
        "experience": {
            "type": "object",
            "properties": {
                "total_years": {"type": "number"},
                "commercial_years": {"type": "number"},
                "leadership_years": {"type": "number"},
                "architecture_years": {"type": "number"},
                "ai_years": {"type": "number"},
                "devops_years": {"type": "number"},
                "backend_years": {"type": "number"},
                "frontend_years": {"type": "number"},
                "analytics_years": {"type": "number"},
            },
        },
        "skills": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "category": {"type": "string"},
                    "confidence": {"type": "number"},
                },
            },
        },
        "domains": {"type": "array", "items": {"type": "string"}},
        "strengths": {"type": "array", "items": {"type": "string"}},
        "weaknesses": {"type": "array", "items": {"type": "string"}},
        "preferred_roles": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "priority": {"type": "string", "enum": ["high", "medium", "low"]},
                },
            },
        },
        "search_strategy": {
            "type": "object",
            "properties": {
                "include_keywords": {"type": "array", "items": {"type": "string"}},
                "exclude_keywords": {"type": "array", "items": {"type": "string"}},
                "preferred_roles": {"type": "array", "items": {"type": "string"}},
                "excluded_roles": {"type": "array", "items": {"type": "string"}},
            },
        },
        "prompt_context": {"type": "string"},
        "ai_summary": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Human-readable bullet points in Russian summarizing what AI understood",
        },
        "companies_count": {"type": "integer"},
        "projects_count": {"type": "integer"},
    },
    "required": ["primary_specialization", "level", "skills"],
}


class ResumeAnalysisService:
    def __init__(
        self,
        llm: LLMService,
        file_storage: ResumeFileStorage,
        resume_repo: ResumeFileRepository,
        profile_repo: CandidateProfileRepository,
        job_store: AnalysisJobStore,
        event_bus: EventBus,
    ):
        self._llm = llm
        self._storage = file_storage
        self._resumes = resume_repo
        self._profiles = profile_repo
        self._jobs = job_store
        self._events = event_bus

    async def start_upload(self, user_id: UUID, filename: str, pdf_data: bytes) -> AnalysisJob:
        file_id, path = self._storage.save(user_id, filename, pdf_data)
        resume_file = ResumeFile(
            id=file_id,
            user_id=user_id,
            filename=filename,
            storage_path=str(path),
        )
        await self._resumes.save_file(resume_file)

        old_profile = await self._profiles.get_profile(user_id)
        if old_profile:
            await self._profiles.add_history_entry(user_id, old_profile, trigger="reanalysis")

        # Replace previous profile on new upload
        await self._profiles.delete_profile(user_id)

        job = AnalysisJob(user_id=user_id, resume_file_id=file_id)
        await self._jobs.create(job)
        asyncio.create_task(self._run_pipeline(job, resume_file, pdf_data))
        return job

    async def get_job(self, job_id: UUID) -> AnalysisJob | None:
        return await self._jobs.get(job_id)

    async def get_profile(self, user_id: UUID) -> CandidateProfile | None:
        return await self._profiles.get_profile(user_id)

    async def _advance(self, job: AnalysisJob, step_key: str, step_label: str) -> None:
        job.current_step = step_label
        if step_key not in job.steps_completed:
            job.steps_completed.append(step_key)
        job.progress = int(len(job.steps_completed) / len(ANALYSIS_STEPS) * 100)
        await self._jobs.update(job)

    async def _run_pipeline(self, job: AnalysisJob, resume_file: ResumeFile, pdf_data: bytes) -> None:
        started = time.perf_counter()
        settings = get_settings()
        text = ""
        try:
            job.status = AnalysisStatus.EXTRACTING
            await self._advance(job, "extract_text", "Извлекаю текст")
            text = extract_text_from_pdf(pdf_data)
            resume_file.extracted_text = text
            await self._resumes.save_file(resume_file)

            job.status = AnalysisStatus.ANALYZING
            for key, label in ANALYSIS_STEPS[1:]:
                await self._advance(job, key, label)
                await asyncio.sleep(0.3)  # allow UI to poll progress

            try:
                analysis = await self._analyze_with_llm(text)
                partial = False
            except Exception as llm_exc:
                if text.strip() and is_rate_limit_error(llm_exc):
                    logger.warning(
                        "resume_analysis_llm_rate_limited_using_fallback",
                        user_id=str(job.user_id),
                    )
                    analysis = build_fallback_analysis(text)
                    partial = True
                else:
                    raise

            profile = self._build_profile(
                job.user_id,
                resume_file.id,
                analysis,
                resume_filename=resume_file.filename,
                settings=settings,
                duration_seconds=time.perf_counter() - started,
            )
            profile.prompt_context = analysis.get("prompt_context") or build_prompt_context(profile)

            await self._profiles.save_profile(profile)
            await self._profiles.add_history_entry(job.user_id, profile, trigger="analysis")
            job.profile = profile
            job.status = AnalysisStatus.COMPLETED
            job.progress = 100
            job.current_step = "Готово"
            if partial:
                job.error = (
                    "Полный AI-анализ недоступен (лимит API). "
                    "Создан предварительный профиль — пересканируйте через 1–2 мин."
                )
            await self._jobs.update(job)

            await self._events.publish(
                ResumeUpdated(resume_id=resume_file.id, user_id=job.user_id, version=profile.version)
            )
            logger.info("resume_analysis_completed", user_id=str(job.user_id))

        except Exception as exc:
            logger.exception("resume_analysis_failed", user_id=str(job.user_id))
            job.status = AnalysisStatus.FAILED
            job.error = _friendly_analysis_error(exc)
            await self._jobs.update(job)

    async def _analyze_with_llm(self, resume_text: str) -> dict[str, Any]:
        system = """You are Ugra's resume analysis engine. Analyze the resume thoroughly and return structured JSON.
Determine true specialization (not just job title), level with rationale, experience breakdown,
categorized tech stack with confidence 0-100, domains, strengths, weaknesses,
preferred roles with priority (high/medium/low), and search strategy (include/exclude keywords).
Also generate ai_summary: 6-10 bullet points in Russian (starting with «•» concepts, plain language)
describing what you understood about the candidate for the user to verify.
Estimate companies_count and projects_count from resume content.
Be honest about weaknesses. Do not invent experience not in the resume."""

        user = f"Analyze this resume:\n\n{resume_text[:12000]}"
        return await self._llm.generate_structured(system, user, ANALYSIS_SCHEMA)

    def _build_profile(
        self,
        user_id: UUID,
        resume_file_id: UUID,
        data: dict[str, Any],
        *,
        resume_filename: str = "",
        settings: Settings | None = None,
        duration_seconds: float = 0.0,
    ) -> CandidateProfile:
        exp_data = data.get("experience") or {}
        strat_data = data.get("search_strategy") or {}

        try:
            level = SpecialistLevel(data.get("level", "middle"))
        except ValueError:
            level = SpecialistLevel.MIDDLE

        settings = settings or get_settings()
        skills = [
            TechSkill(
                name=s.get("name", ""),
                category=s.get("category", "Other"),
                confidence=float(s.get("confidence", 50)),
            )
            for s in data.get("skills", [])
            if s.get("name")
        ]

        roles = [
            RolePriority(title=r.get("title", ""), priority=r.get("priority", "medium"))
            for r in data.get("preferred_roles", [])
            if r.get("title")
        ]

        domains = data.get("domains", [])
        ai_summary = [s.lstrip("• ").strip() for s in data.get("ai_summary", []) if s]

        return CandidateProfile(
            user_id=user_id,
            identity=CandidateIdentity(
                full_name=data.get("full_name", ""),
                primary_specialization=data.get("primary_specialization", ""),
                secondary_specializations=data.get("secondary_specializations", []),
                level=level,
                level_rationale=data.get("level_rationale", ""),
            ),
            experience=ExperienceBreakdown(
                total_years=float(exp_data.get("total_years", 0)),
                commercial_years=float(exp_data.get("commercial_years", 0)),
                leadership_years=float(exp_data.get("leadership_years", 0)),
                architecture_years=float(exp_data.get("architecture_years", 0)),
                ai_years=float(exp_data.get("ai_years", 0)),
                devops_years=float(exp_data.get("devops_years", 0)),
                backend_years=float(exp_data.get("backend_years", 0)),
                frontend_years=float(exp_data.get("frontend_years", 0)),
                analytics_years=float(exp_data.get("analytics_years", 0)),
            ),
            skills=skills,
            domains=domains,
            strengths=data.get("strengths", []),
            weaknesses=data.get("weaknesses", []),
            preferred_roles=roles,
            search_strategy=SearchStrategy(
                include_keywords=strat_data.get("include_keywords", []),
                exclude_keywords=strat_data.get("exclude_keywords", []),
                preferred_roles=strat_data.get("preferred_roles", []),
                excluded_roles=strat_data.get("excluded_roles", []),
            ),
            prompt_context=data.get("prompt_context", ""),
            ai_summary=ai_summary,
            analysis_meta=AnalysisMeta(
                model=settings.default_llm_model,
                provider=settings.default_llm_provider,
                duration_seconds=round(duration_seconds, 1),
                resume_filename=resume_filename,
            ),
            analysis_stats=AnalysisStats(
                skills_count=len(skills),
                technologies_count=len(skills),
                companies_count=int(data.get("companies_count", 0)),
                projects_count=int(data.get("projects_count", 0)),
                domains_count=len(domains),
                roles_count=len(roles),
            ),
            resume_file_id=resume_file_id,
            version=1,
        )


def _friendly_analysis_error(exc: BaseException) -> str:
    msg = str(exc)
    lower = msg.lower()
    if "429" in msg or "rate limit" in lower:
        return "Превышен лимит запросов к AI (429). Подождите 1–2 минуты и загрузите резюме снова."
    if "401" in msg or "unauthorized" in lower or "invalid api key" in lower:
        return "Неверный API-ключ LLM. Проверьте OPENAI_API_KEY в .env."
    if "timeout" in lower or "timed out" in lower:
        return "AI не ответил вовремя. Попробуйте ещё раз."
    return msg[:500]
