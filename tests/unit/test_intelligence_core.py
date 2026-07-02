"""Tests for Ugra Intelligence Core."""

from uuid import uuid4

import pytest

from ugra.application.intelligence.cognition_engine import CognitionEngine
from ugra.application.intelligence.goal_manager import GoalManager
from ugra.application.intelligence.personality_engine import PersonalityEngine
from ugra.core.events.bus import EventBus
from ugra.core.tools.base import ToolContext, ToolName, ToolRegistry
from ugra.core.tools.implementations import NotificationTool
from ugra.domain.goals import Goal, GoalType
from ugra.domain.memory import CompanyPreference, LongTermMemory
from ugra.domain.personality import AudienceType, CommunicationMode
from ugra.domain.reasoning import ReasoningCategory
from ugra.infrastructure.llm.completion_gateway import CompletionGateway
from ugra.infrastructure.persistence.repositories.goal_repository import InMemoryGoalRepository
from ugra.infrastructure.persistence.repositories.memory_repository import InMemoryMemoryRepository
from ugra.infrastructure.prompts.manager import PromptManager


class StubGateway(CompletionGateway):
    def __init__(self):
        pass

    @property
    def provider(self) -> str:
        return "stub"

    @property
    def model(self) -> str:
        return "stub"

    async def complete_text(self, system_prompt: str, user_prompt: str, **kwargs) -> str:
        return "planned action"

    async def complete_json(self, system_prompt: str, user_prompt: str, schema, **kwargs) -> dict:
        return {
            "steps": [{"action": "search", "tool": "job_search", "rationale": "find jobs"}],
            "priority": "high",
        }


@pytest.fixture
def cognition():
    return CognitionEngine(StubGateway(), PromptManager())


@pytest.fixture
def personality():
    return PersonalityEngine()


@pytest.fixture
def goal_manager():
    return GoalManager(InMemoryGoalRepository(), EventBus())


def test_personality_hunter_mode_for_owner(personality):
    audience = personality.detect_audience("owner", {"is_owner": True})
    assert personality.resolve_mode(audience) == CommunicationMode.HUNTER


def test_personality_professional_mode_for_hr(personality):
    audience = personality.detect_audience("hr")
    assert personality.resolve_mode(audience) == CommunicationMode.PROFESSIONAL


def test_personality_removes_forbidden_words_in_professional_mode(personality):
    text = "Мур... Я AI-бот, напишу отклик."
    result = personality.apply(text, audience=AudienceType.HR, is_professional_content=True)
    assert "мур" not in result.lower()
    assert "ai" not in result.lower()


def test_personality_hunter_can_add_expression(personality):
    text = "Нашла отличную вакансию для тебя, смотри результаты поиска."
    result = personality.apply(text, audience=AudienceType.OWNER)
    assert len(result) >= len(text)


@pytest.mark.asyncio
async def test_cognition_evaluates_vacancy_fit(cognition):
    user_id = uuid4()
    memory = LongTermMemory(user_id=user_id)
    job = {"id": str(uuid4()), "company": "BadCorp", "match_score": 80}
    memory.ignored_companies.append(CompanyPreference(company="BadCorp", reason="toxic"))

    should_apply, rationale = cognition.evaluate_vacancy_fit(user_id, job, memory, None)
    assert should_apply is False
    assert "ignore" in rationale.lower()


@pytest.mark.asyncio
async def test_cognition_records_reasoning(cognition):
    user_id = uuid4()
    memory = LongTermMemory(user_id=user_id)
    job = {"id": str(uuid4()), "company": "GoodCorp", "match_score": 85, "technologies": ["python"]}

    cognition.evaluate_vacancy_fit(user_id, job, memory, None)
    records = cognition.get_reasoning(user_id)
    assert len(records) == 1
    assert records[0].category == ReasoningCategory.VACANCY_SELECTION


@pytest.mark.asyncio
async def test_cognition_select_resume(cognition):
    user_id = uuid4()
    resumes = [
        {"id": "1", "title": "AI Engineer", "skills": ["python", "rag", "langgraph"]},
        {"id": "2", "title": ".NET", "skills": ["csharp", "dotnet"]},
    ]
    job = {"title": "ML Engineer", "technologies": ["python", "rag"]}

    best = cognition.select_resume(user_id, resumes, job)
    assert best is not None
    assert best["title"] == "AI Engineer"


@pytest.mark.asyncio
async def test_goal_manager_sets_active_goal(goal_manager):
    user_id = uuid4()
    goal = await goal_manager.set_goal(user_id, "Get AI Engineer job", GoalType.FIND_JOB)
    active = await goal_manager.get_active_goal(user_id)
    assert active is not None
    assert active.title == "Get AI Engineer job"


@pytest.mark.asyncio
async def test_goal_alignment(goal_manager):
    user_id = uuid4()
    await goal_manager.set_goal(user_id, "Find job", GoalType.FIND_JOB)
    assert await goal_manager.align_action(user_id, "search vacancies") is True
    assert await goal_manager.align_action(user_id, "cook dinner") is False


@pytest.mark.asyncio
async def test_memory_repository():
    repo = InMemoryMemoryRepository()
    user_id = uuid4()
    memory = await repo.get_or_create(user_id)
    assert memory.user_id == user_id

    memory.learned_technologies.append(
        __import__("ugra.domain.memory", fromlist=["TechnologyRecord"]).TechnologyRecord(name="RAG")
    )
    saved = await repo.save(memory)
    loaded = await repo.get_by_user(user_id)
    assert loaded is not None
    assert len(loaded.learned_technologies) == 1


@pytest.mark.asyncio
async def test_tool_registry_auto_register():
    registry = ToolRegistry()
    registry.register(NotificationTool())
    result = await registry.execute(
        ToolName.NOTIFICATION,
        ToolContext(user_id=uuid4(), agent_name="test", parameters={"channel": "telegram", "message": "hi"}),
    )
    assert result.success is True


def test_prompt_manager_loads_versioned_prompt():
    pm = PromptManager()
    template = pm.load("career_agent")
    assert "Career Agent" in template.system


def test_prompt_manager_renders_variables():
    pm = PromptManager()
    rendered = pm.render("career_agent", goal_context="Find AI job", memory_context="empty")
    assert "Find AI job" in rendered


@pytest.mark.asyncio
async def test_cognition_plan_actions(cognition):
    user_id = uuid4()
    memory = LongTermMemory(user_id=user_id)
    goal = Goal(user_id=user_id, title="Find AI Engineer job", goal_type=GoalType.FIND_JOB)

    steps = await cognition.plan_actions(user_id, goal, memory, ["job_search", "notification"])
    assert len(steps) >= 1
    assert steps[0]["tool"] == "job_search"
