"""Cover Letter Agent — personalized cover letter generation."""

from ugra.agents.base.registry import AgentCapability, AgentContext, AgentResponse, BaseAgent
from ugra.domain.entities import JobVacancy
from ugra.infrastructure.llm.service import LLMService


class CoverLetterAgent(BaseAgent):
    def __init__(self, llm: LLMService):
        self._llm = llm

    @property
    def name(self) -> str:
        return "cover_letter_agent"

    @property
    def capabilities(self) -> list[AgentCapability]:
        return [AgentCapability.COVER_LETTER]

    async def can_handle(self, context: AgentContext) -> float:
        keywords = ["cover", "letter", "письм", "сопровод"]
        return 0.85 if any(k in context.message.lower() for k in keywords) else 0.05

    async def invoke(self, context: AgentContext) -> AgentResponse:
        job = context.metadata.get("job")
        resume = context.metadata.get("resume")
        if not job or not resume:
            return AgentResponse(
                agent_name=self.name,
                content="Для генерации письма выберите вакансию и резюме.",
            )

        letter = await self.generate(
            job=job,
            resume_content=resume.get("content", ""),
            user_experience=context.metadata.get("experience", ""),
            company_style=context.metadata.get("company_style", "formal"),
        )
        return AgentResponse(
            agent_name=self.name,
            content=f"📝 *Сопроводительное письмо:*\n\n{letter}",
            data={"cover_letter": letter},
            capabilities_used=[AgentCapability.COVER_LETTER],
        )

    async def generate(
        self,
        job: dict | JobVacancy,
        resume_content: str,
        user_experience: str = "",
        company_style: str = "formal",
    ) -> str:
        title = job.title if isinstance(job, JobVacancy) else job.get("title", "")
        company = job.company if isinstance(job, JobVacancy) else job.get("company", "")
        description = job.description if isinstance(job, JobVacancy) else job.get("description", "")

        prompt = f"""Write a personalized cover letter in Russian.

Job: {title} at {company}
Description: {description[:1500]}
Candidate experience: {user_experience}
Resume highlights: {resume_content[:1000]}
Company style: {company_style}

Be specific, professional, and concise (max 300 words)."""

        return await self._llm.generate(
            "You write compelling, personalized cover letters.", prompt
        )
