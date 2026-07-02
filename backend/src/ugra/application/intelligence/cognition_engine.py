"""Cognition Engine — Ugra-owned planning and reasoning.

The LLM is used only as a text generator for specific sub-tasks.
Planning logic, goal alignment, and decision recording belong to Ugra.
"""

from uuid import UUID

from ugra.core.logging.setup import get_logger
from ugra.domain.goals import Goal
from ugra.domain.memory import LongTermMemory
from ugra.domain.reasoning import ReasoningCategory, ReasoningRecord
from ugra.infrastructure.llm.completion_gateway import CompletionGateway
from ugra.infrastructure.prompts.manager import PromptManager

logger = get_logger(__name__)


class CognitionEngine:
    """Central intelligence module — replaceable LLM, owned logic."""

    def __init__(
        self,
        gateway: CompletionGateway,
        prompt_manager: PromptManager,
    ):
        self._gateway = gateway
        self._prompts = prompt_manager
        self._reasoning_log: list[ReasoningRecord] = []

    @property
    def reasoning_history(self) -> list[ReasoningRecord]:
        return list(self._reasoning_log)

    def get_reasoning(self, user_id: UUID, limit: int = 20) -> list[ReasoningRecord]:
        return [r for r in self._reasoning_log if r.user_id == user_id][-limit:]

    async def plan_actions(
        self,
        user_id: UUID,
        goal: Goal | None,
        memory: LongTermMemory,
        available_tools: list[str],
        agent_name: str = "orchestrator",
    ) -> list[dict]:
        goal_text = goal.title if goal else "No active goal"
        memory_summary = self.summarize_memory(memory)
        tools_text = ", ".join(available_tools)

        system = self._prompts.render(
            "cognition",
            goal=goal_text,
            available_tools=tools_text,
            memory_summary=memory_summary,
        )

        schema = {
            "steps": [{"action": "str", "tool": "str|null", "rationale": "str"}],
            "priority": "high|medium|low",
        }

        try:
            plan = await self._gateway.complete_json(
                system,
                "Create an action plan for the current goal.",
                schema,
            )
        except Exception:
            logger.exception("plan_generation_failed")
            plan = self._fallback_plan(goal, available_tools)

        steps = plan.get("steps", [])
        self._record(
            agent_name=agent_name,
            user_id=user_id,
            category=ReasoningCategory.GOAL_ALIGNMENT,
            decision=f"Plan with {len(steps)} steps",
            rationale=f"Goal: {goal_text}. Tools: {tools_text}",
            confidence=0.8,
            context={"plan": plan},
        )
        return steps

    def evaluate_vacancy_fit(
        self,
        user_id: UUID,
        job: dict,
        memory: LongTermMemory,
        goal: Goal | None,
        agent_name: str = "career_agent",
    ) -> tuple[bool, str]:
        company = job.get("company", "").lower()
        for ignored in memory.ignored_companies:
            if ignored.company.lower() == company:
                rationale = f"Company '{company}' is in ignore list: {ignored.reason}"
                self._record(
                    agent_name=agent_name,
                    user_id=user_id,
                    category=ReasoningCategory.APPLICATION_DECISION,
                    decision="skip",
                    rationale=rationale,
                    confidence=1.0,
                    context={"job_id": job.get("id")},
                )
                return False, rationale

        match_score = job.get("match_score", 0)
        threshold = 60.0
        if goal and goal.goal_type.value == "find_job":
            threshold = 50.0

        should_apply = match_score >= threshold
        rationale = (
            f"Match score {match_score}% {'meets' if should_apply else 'below'} threshold {threshold}%"
        )
        self._record(
            agent_name=agent_name,
            user_id=user_id,
            category=ReasoningCategory.VACANCY_SELECTION,
            decision="apply" if should_apply else "skip",
            rationale=rationale,
            confidence=match_score / 100,
            context={"job": job},
        )
        return should_apply, rationale

    def select_resume(
        self,
        user_id: UUID,
        resumes: list[dict],
        job: dict,
        agent_name: str = "resume_agent",
    ) -> dict | None:
        if not resumes:
            self._record(
                agent_name=agent_name,
                user_id=user_id,
                category=ReasoningCategory.RESUME_CHOICE,
                decision="none",
                rationale="No resumes available",
                confidence=1.0,
            )
            return None

        job_tech = set(t.lower() for t in job.get("technologies", []))
        best = max(
            resumes,
            key=lambda r: len(set(s.lower() for s in r.get("skills", [])) & job_tech),
        )
        overlap = set(s.lower() for s in best.get("skills", [])) & job_tech
        rationale = f"Resume '{best.get('title')}' has {len(overlap)} matching technologies"
        self._record(
            agent_name=agent_name,
            user_id=user_id,
            category=ReasoningCategory.RESUME_CHOICE,
            decision=best.get("title", "unknown"),
            rationale=rationale,
            confidence=len(overlap) / max(len(job_tech), 1),
            context={"resume_id": best.get("id")},
        )
        return best

    def summarize_memory(self, memory: LongTermMemory) -> str:
        parts = [
            f"vacancies: {len(memory.vacancy_history)}",
            f"interviews: {len(memory.interview_history)}",
            f"offers: {len(memory.offer_history)}",
            f"ignored companies: {len(memory.ignored_companies)}",
            f"learned tech: {len(memory.learned_technologies)}",
        ]
        return "; ".join(parts)

    def _fallback_plan(self, goal: Goal | None, tools: list[str]) -> dict:
        steps = []
        if goal and "job" in goal.title.lower():
            if "job_search" in tools:
                steps.append({"action": "search_vacancies", "tool": "job_search", "rationale": "Active job search goal"})
        if not steps:
            steps.append({"action": "check_messages", "tool": "notification", "rationale": "Default autonomous check"})
        return {"steps": steps, "priority": "medium"}

    def _record(
        self,
        agent_name: str,
        user_id: UUID,
        category: ReasoningCategory,
        decision: str,
        rationale: str,
        confidence: float,
        context: dict | None = None,
    ) -> ReasoningRecord:
        record = ReasoningRecord(
            agent_name=agent_name,
            user_id=user_id,
            category=category,
            decision=decision,
            rationale=rationale,
            confidence=confidence,
            context=context or {},
        )
        self._reasoning_log.append(record)
        logger.info(
            "reasoning_recorded",
            agent=agent_name,
            category=category.value,
            decision=decision,
        )
        return record
