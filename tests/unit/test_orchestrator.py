"""Tests for agent registry and orchestrator."""

from uuid import uuid4

import pytest

from ugra.agents.base.registry import AgentCapability, AgentContext, AgentRegistry, AgentResponse, BaseAgent
from ugra.agents.orchestrator.intelligence_orchestrator import IntelligenceOrchestrator


class StubAgent(BaseAgent):
    def __init__(self, name: str, capability: AgentCapability, confidence: float):
        self._name = name
        self._capability = capability
        self._confidence = confidence

    @property
    def name(self) -> str:
        return self._name

    @property
    def capabilities(self) -> list[AgentCapability]:
        return [self._capability]

    async def can_handle(self, context: AgentContext) -> float:
        return self._confidence

    async def invoke(self, context: AgentContext) -> AgentResponse:
        return AgentResponse(agent_name=self._name, content=f"Handled by {self._name}")


@pytest.fixture
def registry():
    reg = AgentRegistry()
    reg.register(StubAgent("career", AgentCapability.JOB_SEARCH, 0.9))
    reg.register(StubAgent("resume", AgentCapability.RESUME, 0.1))
    return reg


@pytest.mark.asyncio
async def test_orchestrator_routes_to_best_agent(registry):
    from ugra.application.intelligence.cognition_engine import CognitionEngine
    from ugra.application.intelligence.goal_manager import GoalManager
    from ugra.application.intelligence.personality_engine import PersonalityEngine
    from ugra.core.events.bus import EventBus
    from ugra.core.tools.base import ToolRegistry
    from ugra.infrastructure.persistence.repositories.goal_repository import InMemoryGoalRepository
    from ugra.infrastructure.persistence.repositories.memory_repository import InMemoryMemoryRepository
    from ugra.infrastructure.prompts.manager import PromptManager
    from tests.unit.test_intelligence_core import StubGateway

    orchestrator = IntelligenceOrchestrator(
        registry=registry,
        cognition=CognitionEngine(StubGateway(), PromptManager()),
        goal_manager=GoalManager(InMemoryGoalRepository(), EventBus()),
        memory_repo=InMemoryMemoryRepository(),
        tool_registry=ToolRegistry(),
        personality=PersonalityEngine(),
        event_bus=EventBus(),
    )
    context = AgentContext(user_id=uuid4(), message="find jobs")
    response = await orchestrator.route(context)
    assert response.agent_name == "career"


@pytest.mark.asyncio
async def test_orchestrator_low_confidence(registry):
    from ugra.application.intelligence.cognition_engine import CognitionEngine
    from ugra.application.intelligence.goal_manager import GoalManager
    from ugra.application.intelligence.personality_engine import PersonalityEngine
    from ugra.core.events.bus import EventBus
    from ugra.core.tools.base import ToolRegistry
    from ugra.infrastructure.persistence.repositories.goal_repository import InMemoryGoalRepository
    from ugra.infrastructure.persistence.repositories.memory_repository import InMemoryMemoryRepository
    from ugra.infrastructure.prompts.manager import PromptManager
    from tests.unit.test_intelligence_core import StubGateway

    low_conf_registry = AgentRegistry()
    low_conf_registry.register(StubAgent("weak", AgentCapability.HR, 0.1))
    orchestrator = IntelligenceOrchestrator(
        registry=low_conf_registry,
        cognition=CognitionEngine(StubGateway(), PromptManager()),
        goal_manager=GoalManager(InMemoryGoalRepository(), EventBus()),
        memory_repo=InMemoryMemoryRepository(),
        tool_registry=ToolRegistry(),
        personality=PersonalityEngine(),
        event_bus=EventBus(),
    )

    context = AgentContext(user_id=uuid4(), message="hello")
    response = await orchestrator.route(context)
    assert response.agent_name == "orchestrator"


def test_agent_registry_by_capability(registry):
    agents = registry.by_capability(AgentCapability.JOB_SEARCH)
    assert len(agents) == 1
    assert agents[0].name == "career"
