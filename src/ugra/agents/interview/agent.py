"""Interview Agent — preparation after application."""

from ugra.agents.base.registry import AgentCapability, AgentContext, AgentResponse, BaseAgent
from ugra.domain.entities import InterviewPrep, JobVacancy
from ugra.infrastructure.llm.service import LLMService


class InterviewAgent(BaseAgent):
    def __init__(self, llm: LLMService):
        self._llm = llm

    @property
    def name(self) -> str:
        return "interview_agent"

    @property
    def capabilities(self) -> list[AgentCapability]:
        return [AgentCapability.INTERVIEW]

    async def can_handle(self, context: AgentContext) -> float:
        keywords = ["interview", "собес", "/interview"]
        return 0.9 if any(k in context.message.lower() for k in keywords) else 0.05

    async def invoke(self, context: AgentContext) -> AgentResponse:
        job = context.metadata.get("job")
        if not job:
            return AgentResponse(
                agent_name=self.name,
                content="Выберите вакансию для подготовки к интервью.",
            )

        prep = await self.prepare(job, context.metadata.get("skills", []))
        content = self._format_prep(prep)
        return AgentResponse(
            agent_name=self.name,
            content=content,
            data={
                "questions": prep.questions,
                "answers": prep.answers,
                "topics": prep.topics,
                "checklist": prep.checklist,
            },
            capabilities_used=[AgentCapability.INTERVIEW],
        )

    async def prepare(self, job: dict | JobVacancy, user_skills: list[str]) -> InterviewPrep:
        title = job.title if isinstance(job, JobVacancy) else job.get("title", "")
        company = job.company if isinstance(job, JobVacancy) else job.get("company", "")
        description = job.description if isinstance(job, JobVacancy) else job.get("description", "")

        schema = {
            "questions": ["likely interview questions"],
            "answers": ["suggested answers matching user skills"],
            "topics": ["topics to review"],
            "checklist": ["preparation checklist items"],
        }

        prompt = f"""Prepare interview materials for:

Position: {title} at {company}
Description: {description[:2000]}
Candidate skills: {', '.join(user_skills)}

Generate 5-7 questions, model answers, review topics, and a checklist."""

        data = await self._llm.generate_structured(
            "You are an expert interview coach.", prompt, schema
        )

        return InterviewPrep(
            questions=data.get("questions", []),
            answers=data.get("answers", []),
            topics=data.get("topics", []),
            checklist=data.get("checklist", []),
        )

    def _format_prep(self, prep: InterviewPrep) -> str:
        lines = ["🎯 *Подготовка к интервью:*\n"]

        lines.append("*Возможные вопросы:*")
        for i, q in enumerate(prep.questions[:5], 1):
            lines.append(f"{i}. {q}")

        lines.append("\n*Темы для повторения:*")
        for t in prep.topics[:5]:
            lines.append(f"• {t}")

        lines.append("\n*Чек-лист:*")
        for c in prep.checklist[:5]:
            lines.append(f"☐ {c}")

        return "\n".join(lines)
