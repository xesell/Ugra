"""In-memory UI state for applications, resumes, cover letters, settings."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from ugra.application.ui.persistence import default_ui_state_path, load_ui_state, save_ui_state
from ugra.core.logging.setup import get_logger

logger = get_logger(__name__)


@dataclass
class ApplicationRecord:
    id: str
    job_id: str
    company: str
    title: str
    url: str
    source: str
    status: str
    sent_at: str
    updated_at: str
    resume_title: str = ""
    cover_letter_preview: str = ""
    history: list[dict[str, str]] = field(default_factory=list)
    employer_reply: str = ""


@dataclass
class ResumeRecord:
    id: str
    title: str
    skills: list[str]
    experience_years: int
    content: str
    is_default: bool = False
    version: int = 1
    updated_at: str = ""


@dataclass
class CoverLetterTemplate:
    id: str
    title: str
    content: str
    updated_at: str
    suitable_for: list[str]
    usage_count: int = 0


@dataclass
class SourceStatus:
    id: str
    name: str
    connected: bool
    last_sync: str | None
    token_expires: str | None
    vacancies_found: int
    enabled: bool = True


@dataclass
class UISettings:
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o"
    llm_api_key: str = ""
    temperature: float = 0.7
    max_tokens: int = 4096
    search_interval_hours: int = 6
    salary_min: int = 0
    excluded_companies: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    minus_words: list[str] = field(default_factory=list)
    cities: list[str] = field(default_factory=list)
    countries: list[str] = field(default_factory=list)
    auto_apply: bool = False
    apply_after_ai_review: bool = True
    min_match_percent: int = 80
    apply_delay_seconds: int = 30
    max_applications_per_day: int = 20
    work_hours_start: str = "09:00"
    work_hours_end: str = "18:00"
    telegram_token: str = ""
    telegram_chat_id: str = ""
    proxy_type: str = ""
    proxy_host: str = ""
    proxy_login: str = ""
    proxy_password: str = ""


class UIStateStore:
    def __init__(self, path: Path | None = None) -> None:
        self._path = path or default_ui_state_path()
        self._applications: dict[str, ApplicationRecord] = {}
        self._resumes: dict[str, ResumeRecord] = {}
        self._cover_letters: dict[str, CoverLetterTemplate] = {}
        self._ignored_jobs: set[str] = set()
        self.settings = UISettings()
        if not self._load_from_disk():
            self._seed_demo_data()
            self._persist()

    def _load_from_disk(self) -> bool:
        raw = load_ui_state(self._path)
        if not raw:
            return False
        try:
            for item in raw.get("applications", []):
                rec = ApplicationRecord(**item)
                self._applications[rec.id] = rec
            for item in raw.get("resumes", []):
                rec = ResumeRecord(**item)
                self._resumes[rec.id] = rec
            for item in raw.get("cover_letters", []):
                rec = CoverLetterTemplate(**item)
                self._cover_letters[rec.id] = rec
            self._ignored_jobs = set(raw.get("ignored_jobs", []))
            if settings_data := raw.get("settings"):
                self.settings = UISettings(**{**asdict(UISettings()), **settings_data})
            logger.info(
                "ui_state_loaded",
                path=str(self._path),
                cover_letters=len(self._cover_letters),
            )
            return True
        except (TypeError, KeyError) as exc:
            logger.warning("ui_state_parse_failed", error=str(exc))
            return False

    def _persist(self) -> None:
        data = {
            "applications": [asdict(a) for a in self._applications.values()],
            "resumes": [asdict(r) for r in self._resumes.values()],
            "cover_letters": [asdict(c) for c in self._cover_letters.values()],
            "ignored_jobs": list(self._ignored_jobs),
            "settings": asdict(self.settings),
        }
        save_ui_state(self._path, data)

    def _ts(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _seed_demo_data(self) -> None:
        now = self._ts()
        for title, skills in [
            ("Backend", ["Python", "FastAPI", "PostgreSQL", "Docker"]),
            ("DevOps", ["Kubernetes", "Terraform", "CI/CD", "AWS"]),
            ("Team Lead", ["Leadership", "Architecture", "Hiring", "Python"]),
        ]:
            rid = str(uuid4())
            self._resumes[rid] = ResumeRecord(
                id=rid,
                title=title,
                skills=skills,
                experience_years=5,
                content=f"Resume content for {title} role.",
                is_default=title == "Backend",
                version=1,
                updated_at=now,
            )

        cl_id = str(uuid4())
        self._cover_letters[cl_id] = CoverLetterTemplate(
            id=cl_id,
            title="Formal IT",
            content="Dear Hiring Manager,\n\nI am excited to apply...",
            updated_at=now,
            suitable_for=["Backend", "Senior Python"],
            usage_count=12,
        )

    def list_applications(self) -> list[dict[str, Any]]:
        return [asdict(a) for a in sorted(self._applications.values(), key=lambda x: x.sent_at, reverse=True)]

    def get_application(self, app_id: str) -> ApplicationRecord | None:
        return self._applications.get(app_id)

    def create_application(self, job: dict[str, Any], resume_title: str = "", letter: str = "") -> ApplicationRecord:
        app_id = str(uuid4())
        now = self._ts()
        record = ApplicationRecord(
            id=app_id,
            job_id=str(job.get("id", "")),
            company=job.get("company", ""),
            title=job.get("title", ""),
            url=job.get("url", ""),
            source=job.get("source", "HH"),
            status="sent",
            sent_at=now,
            updated_at=now,
            resume_title=resume_title,
            cover_letter_preview=letter[:200],
            history=[{"time": now, "action": "Отклик отправлен агентом"}],
        )
        self._applications[app_id] = record
        self._persist()
        return record

    def update_application_status(self, app_id: str, status: str, note: str = "") -> ApplicationRecord | None:
        app = self._applications.get(app_id)
        if not app:
            return None
        app.status = status
        app.updated_at = self._ts()
        if note:
            app.history.append({"time": app.updated_at, "action": note})
        self._persist()
        return app

    def list_resumes(self) -> list[dict[str, Any]]:
        return [asdict(r) for r in self._resumes.values()]

    def get_resume(self, resume_id: str) -> ResumeRecord | None:
        return self._resumes.get(resume_id)

    def save_resume(self, data: dict[str, Any]) -> ResumeRecord:
        rid = data.get("id") or str(uuid4())
        existing = self._resumes.get(rid)
        record = ResumeRecord(
            id=rid,
            title=data["title"],
            skills=data.get("skills", []),
            experience_years=int(data.get("experience_years", 0)),
            content=data.get("content", ""),
            is_default=bool(data.get("is_default", False)),
            version=(existing.version + 1) if existing else 1,
            updated_at=self._ts(),
        )
        if record.is_default:
            for r in self._resumes.values():
                r.is_default = False
        self._resumes[rid] = record
        self._persist()
        return record

    def delete_resume(self, resume_id: str) -> bool:
        deleted = self._resumes.pop(resume_id, None) is not None
        if deleted:
            self._persist()
        return deleted

    def list_cover_letters(self) -> list[dict[str, Any]]:
        return [asdict(c) for c in self._cover_letters.values()]

    def save_cover_letter(self, data: dict[str, Any]) -> CoverLetterTemplate:
        cid = data.get("id") or str(uuid4())
        existing = self._cover_letters.get(cid)
        record = CoverLetterTemplate(
            id=cid,
            title=data["title"],
            content=data.get("content", ""),
            updated_at=self._ts(),
            suitable_for=data.get("suitable_for", []),
            usage_count=existing.usage_count if existing else 0,
        )
        self._cover_letters[cid] = record
        self._persist()
        return record

    def delete_cover_letter(self, letter_id: str) -> bool:
        deleted = self._cover_letters.pop(letter_id, None) is not None
        if deleted:
            self._persist()
        return deleted

    def ignore_job(self, job_id: str) -> None:
        self._ignored_jobs.add(job_id)
        self._persist()

    def persist_settings(self) -> None:
        self._persist()


_ui_state_store: UIStateStore | None = None


def get_ui_state_store() -> UIStateStore:
    global _ui_state_store
    if _ui_state_store is None:
        _ui_state_store = UIStateStore()
    return _ui_state_store
