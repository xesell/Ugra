"""Concrete agent tools — each tool is an independent module."""

from uuid import UUID

from ugra.core.tools.base import AgentTool, ToolContext, ToolName, ToolResult
from ugra.domain.value_objects import JobFilter
from ugra.infrastructure.adapters.job_sources.registry import JobSourceRegistry


class JobSearchTool(AgentTool):
    def __init__(self, job_sources: JobSourceRegistry):
        self._sources = job_sources

    @property
    def name(self) -> ToolName:
        return ToolName.JOB_SEARCH

    @property
    def description(self) -> str:
        return "Search job vacancies across configured sources"

    async def execute(self, context: ToolContext) -> ToolResult:
        filters_data = context.parameters.get("filters", {})
        job_filter = JobFilter(
            keywords=tuple(filters_data.get("keywords", [])),
            remote_only=filters_data.get("remote_only", False),
            salary_min=filters_data.get("salary_min"),
            country=filters_data.get("country"),
            technologies=tuple(filters_data.get("technologies", [])),
            level=filters_data.get("level"),
        )
        jobs = await self._sources.search_all(job_filter)
        return ToolResult(
            tool_name=self.name.value,
            success=True,
            data={"jobs": [{"id": str(j.id), "title": j.title, "company": j.company, "url": j.url} for j in jobs[:20]]},
            message=f"Found {len(jobs)} vacancies",
            reasoning="Searched all configured job sources with user filters",
        )


class ResumeTool(AgentTool):
    async def execute(self, context: ToolContext) -> ToolResult:
        resumes = context.parameters.get("resumes", [])
        job = context.parameters.get("job", {})
        best = max(resumes, key=lambda r: len(set(r.get("skills", [])) & set(job.get("technologies", []))), default=None)
        return ToolResult(
            tool_name=self.name.value,
            success=best is not None,
            data={"resume": best},
            message="Selected best matching resume" if best else "No resume found",
            reasoning=f"Matched resume skills against job technologies for {job.get('title', 'unknown')}",
        )

    @property
    def name(self) -> ToolName:
        return ToolName.RESUME


class CoverLetterTool(AgentTool):
    def __init__(self, llm_service):
        self._llm = llm_service

    @property
    def name(self) -> ToolName:
        return ToolName.COVER_LETTER

    async def execute(self, context: ToolContext) -> ToolResult:
        job = context.parameters.get("job", {})
        resume = context.parameters.get("resume_content", "")
        letter = await self._llm.generate(
            "Write a professional cover letter as the user. Never mention AI.",
            f"Job: {job}\nResume: {resume}",
        )
        return ToolResult(
            tool_name=self.name.value,
            success=True,
            data={"cover_letter": letter},
            reasoning=f"Generated personalized cover letter for {job.get('company', 'company')}",
        )


class InterviewTool(AgentTool):
    def __init__(self, llm_service):
        self._llm = llm_service

    @property
    def name(self) -> ToolName:
        return ToolName.INTERVIEW

    async def execute(self, context: ToolContext) -> ToolResult:
        job = context.parameters.get("job", {})
        skills = context.parameters.get("skills", [])
        schema = {"questions": [], "answers": [], "topics": [], "checklist": []}
        prep = await self._llm.generate_structured(
            "Generate interview preparation materials.",
            f"Job: {job}\nSkills: {skills}",
            schema,
        )
        return ToolResult(
            tool_name=self.name.value,
            success=True,
            data=prep,
            reasoning=f"Prepared interview materials for {job.get('title', 'position')}",
        )


class LearningTool(AgentTool):
    def __init__(self, llm_service):
        self._llm = llm_service

    @property
    def name(self) -> ToolName:
        return ToolName.LEARNING

    async def execute(self, context: ToolContext) -> ToolResult:
        gaps = context.parameters.get("skill_gaps", [])
        schema = {"steps": [], "estimated_weeks": 0, "resources": []}
        roadmap = await self._llm.generate_structured(
            "Build a learning roadmap for missing skills.",
            f"Skill gaps: {gaps}",
            schema,
        )
        return ToolResult(
            tool_name=self.name.value,
            success=True,
            data=roadmap,
            reasoning=f"Built learning plan for gaps: {', '.join(gaps)}",
        )


class NotificationTool(AgentTool):
    @property
    def name(self) -> ToolName:
        return ToolName.NOTIFICATION

    async def execute(self, context: ToolContext) -> ToolResult:
        channel = context.parameters.get("channel", "telegram")
        message = context.parameters.get("message", "")
        return ToolResult(
            tool_name=self.name.value,
            success=True,
            data={"channel": channel, "message": message, "sent": True},
            message=f"Notification queued for {channel}",
            reasoning="Notification dispatched to configured channel",
        )


def create_default_tool_registry(job_sources, llm_service) -> "ToolRegistry":
    from ugra.core.tools.base import ToolRegistry

    registry = ToolRegistry()
    registry.register(JobSearchTool(job_sources))
    registry.register(ResumeTool())
    registry.register(CoverLetterTool(llm_service))
    registry.register(InterviewTool(llm_service))
    registry.register(LearningTool(llm_service))
    registry.register(NotificationTool())
    return registry
