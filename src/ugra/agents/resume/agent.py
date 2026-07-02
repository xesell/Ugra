"""Resume Agent — manages multiple resume versions and auto-selection."""

from ugra.agents.base.registry import AgentCapability, AgentContext, AgentResponse, BaseAgent
from ugra.domain.entities import JobVacancy
from ugra.infrastructure.llm.service import LLMService


class ResumeAgent(BaseAgent):
    def __init__(self, llm: LLMService):
        self._llm = llm

    @property
    def name(self) -> str:
        return "resume_agent"

    @property
    def capabilities(self) -> list[AgentCapability]:
        return [AgentCapability.RESUME]

    async def can_handle(self, context: AgentContext) -> float:
        keywords = ["resume", "cv", "резюме", "/resume"]
        return 0.85 if any(k in context.message.lower() for k in keywords) else 0.05

    async def invoke(self, context: AgentContext) -> AgentResponse:
        resumes = context.metadata.get("resumes", [])
        if not resumes:
            return AgentResponse(
                agent_name=self.name,
                content="У вас пока нет сохранённых резюме. Добавьте версии через /settings.",
            )

        lines = ["📄 *Ваши резюме:*\n"]
        for r in resumes:
            lines.append(f"• *{r['title']}* (v{r.get('version', 1)})")
        return AgentResponse(agent_name=self.name, content="\n".join(lines), data={"resumes": resumes})

    async def select_best(self, resumes: list[dict], job: JobVacancy) -> dict | None:
        if not resumes:
            return None
        if len(resumes) == 1:
            return resumes[0]

        prompt = f"""Given job "{job.title}" at {job.company} with skills {job.technologies},
which resume title fits best? Options: {[r['title'] for r in resumes]}
Respond with just the title."""

        title = await self._llm.generate(
            "You select the best resume for a job application.", prompt
        )
        for r in resumes:
            if r["title"].lower() in title.lower():
                return r
        return resumes[0]

    async def adapt_resume(self, resume_content: str, job: JobVacancy) -> str:
        prompt = f"""Adapt this resume for the job:

Job: {job.title} at {job.company}
Requirements: {job.description[:1500]}

Resume:
{resume_content}

Keep factual accuracy. Highlight relevant skills. Output adapted resume only."""

        return await self._llm.generate(
            "You are a professional resume writer.", prompt
        )
