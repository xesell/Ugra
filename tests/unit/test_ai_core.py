"""Tests for AI Core components."""

from uuid import uuid4

import pytest

from ugra.agents.runtime.context import UnifiedAgentContext
from ugra.agents.runtime.memory import AgentMemory
from ugra.agents.runtime.tools import AgentTools
from ugra.application.intelligence.personality_service import PersonalityService
from ugra.application.intelligence.ugra_mood import UgraMoodService
from ugra.core.events.bus import EventBus
from ugra.core.tools.base import ToolContext, ToolName, ToolRegistry
from ugra.core.tools.implementations import NotificationTool
from ugra.domain.agent_state import AgentState
from ugra.infrastructure.persistence.repositories.memory_repository import InMemoryMemoryRepository
from ugra.infrastructure.prompts.manager import PromptManager


@pytest.fixture
def agent_memory():
    return AgentMemory(InMemoryMemoryRepository())


@pytest.fixture
def mood():
    return UgraMoodService()


def test_ugra_mood_labels(mood):
    assert mood.format_status(AgentState.SEARCHING) == "🐆 На охоте..."
    assert mood.format_status(AgentState.WRITING) == "🐆 Готовлю письмо..."
    assert mood.format_status(AgentState.WAITING) == "🐆 Жду твоего решения..."
    assert mood.format_status(AgentState.LEARNING) == "🐆 Изучаю вакансии..."


def test_personality_service_alias():
    service = PersonalityService()
    assert service.resolve_mode(service.detect_audience("owner", {"is_owner": True})).value == "hunter"


@pytest.mark.asyncio
async def test_agent_memory_persists_vacancy(agent_memory):
    user_id = uuid4()
    job_id = uuid4()
    await agent_memory.record_vacancy(user_id, job_id, "AI Engineer", "Yandex", 85.0)
    memory = await agent_memory.load(user_id)
    assert len(memory.vacancy_history) == 1
    assert memory.vacancy_history[0].title == "AI Engineer"


@pytest.mark.asyncio
async def test_agent_memory_persists_rejection(agent_memory):
    user_id = uuid4()
    await agent_memory.record_rejection(user_id, uuid4(), "BadCorp", "toxic culture")
    memory = await agent_memory.load(user_id)
    assert len(memory.rejection_reasons) == 1


@pytest.mark.asyncio
async def test_agent_tools_wrapper():
    registry = ToolRegistry()
    registry.register(NotificationTool())
    tools = AgentTools(registry)
    result = await tools.run(
        ToolName.NOTIFICATION,
        uuid4(),
        "test_agent",
        {"channel": "telegram", "message": "hello"},
    )
    assert result.success is True
    assert "notification" in tools.available


def test_unified_agent_context():
    ctx = UnifiedAgentContext(user_id=uuid4(), message="find jobs", user_skills=["python"])
    ctx.add_turn("user", "find jobs")
    assert ctx.skills == ["python"]
    assert len(ctx.conversation) == 1


def test_prompt_manager_loads_md():
    pm = PromptManager()
    template = pm.load("career_agent")
    assert "Career Agent" in template.system
    assert template.version == "md"


def test_prompt_manager_renders_md_variables():
    pm = PromptManager()
    rendered = pm.render("career_agent", goal_context="AI job", memory_context="empty")
    assert "AI job" in rendered


def test_event_handlers_subscribe():
    from ugra.application.events.handlers import register_event_handlers

    bus = EventBus()
    register_event_handlers(bus, PersonalityService(), UgraMoodService())
    assert len(bus._handlers) >= 7
