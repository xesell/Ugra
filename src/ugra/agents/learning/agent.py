"""Learning Agent — skill gap analysis and learning roadmap."""

from ugra.agents.base.registry import AgentCapability, AgentContext, AgentResponse, BaseAgent
from ugra.domain.entities import LearningRoadmap, SkillGap
from ugra.infrastructure.llm.service import LLMService


class LearningAgent(BaseAgent):
    def __init__(self, llm: LLMService):
        self._llm = llm

    @property
    def name(self) -> str:
        return "learning_agent"

    @property
    def capabilities(self) -> list[AgentCapability]:
        return [AgentCapability.SKILL_GAP, AgentCapability.LEARNING]

    async def can_handle(self, context: AgentContext) -> float:
        keywords = ["learn", "skill", "roadmap", "обуч", "навык", "пробел"]
        return 0.8 if any(k in context.message.lower() for k in keywords) else 0.05

    async def invoke(self, context: AgentContext) -> AgentResponse:
        gaps = context.metadata.get("skill_gaps", [])
        if not gaps:
            return AgentResponse(
                agent_name=self.name,
                content="Сначала проанализируйте вакансию — я определю пробелы в навыках.",
            )

        roadmap = await self.build_roadmap(gaps, context.metadata.get("current_level", "middle"))
        return AgentResponse(
            agent_name=self.name,
            content=self._format_roadmap(roadmap),
            data={"roadmap": {"skills": roadmap.skills, "steps": roadmap.steps}},
            capabilities_used=[AgentCapability.SKILL_GAP, AgentCapability.LEARNING],
        )

    async def analyze_gaps(self, required: list[str], user_skills: list[str]) -> SkillGap:
        user_set = {s.lower() for s in user_skills}
        missing = [s for s in required if s.lower() not in user_set]
        return SkillGap(missing_skills=missing)

    async def build_roadmap(self, missing_skills: list[str], current_level: str) -> LearningRoadmap:
        schema = {
            "steps": ["ordered learning steps"],
            "estimated_weeks": "integer",
            "resources": ["recommended resources"],
        }

        prompt = f"""Build a learning roadmap for these missing skills: {', '.join(missing_skills)}
Current level: {current_level}
Focus on practical, job-relevant learning."""

        data = await self._llm.generate_structured(
            "You create practical tech learning roadmaps.", prompt, schema
        )

        return LearningRoadmap(
            skills=missing_skills,
            steps=data.get("steps", []),
            estimated_weeks=int(data.get("estimated_weeks", 4)),
        )

    def _format_roadmap(self, roadmap: LearningRoadmap) -> str:
        lines = ["📚 *План обучения:*\n"]
        lines.append(f"Оценка: ~{roadmap.estimated_weeks} нед.\n")
        for i, step in enumerate(roadmap.steps, 1):
            lines.append(f"{i}. {step}")
        return "\n".join(lines)
