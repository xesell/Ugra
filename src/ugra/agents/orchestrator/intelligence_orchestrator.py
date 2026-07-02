"""Intelligence Orchestrator — lifecycle, chains, errors, agent switching."""

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from ugra.agents.base.registry import AgentContext, AgentRegistry, AgentResponse, BaseAgent
from ugra.application.intelligence.cognition_engine import CognitionEngine
from ugra.application.intelligence.goal_manager import GoalManager
from ugra.application.intelligence.personality_engine import PersonalityEngine
from ugra.core.events.bus import EventBus
from ugra.core.logging.setup import get_logger
from ugra.core.tools.base import ToolRegistry
from ugra.domain.agent_state import AgentState
from ugra.domain.events import AgentStateChanged
from ugra.domain.repositories.memory import MemoryRepository
from ugra.core.intelligence.agent_runtime import IntelligenceAgent

logger = get_logger(__name__)


@dataclass
class ActionStep:
    agent_name: str | None = None
    tool_name: str | None = None
    action: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass
class OrchestratorState:
    active_agent: str | None = None
    agent_states: dict[str, str] = field(default_factory=dict)


class IntelligenceOrchestrator:
    """Central orchestrator for all Ugra agents."""

    def __init__(
        self,
        registry: AgentRegistry,
        cognition: CognitionEngine,
        goal_manager: GoalManager,
        memory_repo: MemoryRepository,
        tool_registry: ToolRegistry,
        personality: PersonalityEngine,
        event_bus: EventBus,
    ):
        self._registry = registry
        self._cognition = cognition
        self._goals = goal_manager
        self._memory = memory_repo
        self._tools = tool_registry
        self._personality = personality
        self._events = event_bus
        self._state = OrchestratorState()

    @property
    def state(self) -> OrchestratorState:
        for agent in self._registry.agents:
            if isinstance(agent, IntelligenceAgent):
                self._state.agent_states[agent.name] = agent.state.value
        return self._state

    async def start_agent(self, agent_name: str, user_id: UUID) -> None:
        agent = self._registry.get(agent_name)
        if agent and isinstance(agent, IntelligenceAgent):
            await agent.on_start(user_id)
            self._state.active_agent = agent_name

    async def stop_agent(self, agent_name: str, user_id: UUID) -> None:
        agent = self._registry.get(agent_name)
        if agent and isinstance(agent, IntelligenceAgent):
            await agent.on_stop(user_id)
            if self._state.active_agent == agent_name:
                self._state.active_agent = None

    async def route(self, context: AgentContext) -> AgentResponse:
        scores: list[tuple[str, float]] = []
        for agent in self._registry.agents:
            score = await agent.can_handle(context)
            scores.append((agent.name, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        best_name, best_score = scores[0] if scores else (None, 0.0)

        if not best_name or best_score < 0.3:
            greeting = self._personality.greeting(
                self._personality.detect_audience(
                    context.metadata.get("channel", "owner"), context.metadata
                )
            )
            return AgentResponse(
                agent_name="orchestrator",
                content=f"{greeting} I couldn't determine the best agent. Try /jobs, /resume, or /interview.",
                data={"agent_states": self.state.agent_states},
            )

        return await self.invoke_agent(best_name, context)

    async def invoke_agent(self, agent_name: str, context: AgentContext) -> AgentResponse:
        agent = self._registry.get(agent_name)
        if not agent:
            return AgentResponse(agent_name="orchestrator", content=f"Agent '{agent_name}' not found.")

        self._state.active_agent = agent_name
        logger.info("agent_invoked", agent=agent_name, user_id=str(context.user_id))

        try:
            response = await agent.invoke(context)
            return response
        except Exception as exc:
            logger.exception("agent_invocation_failed", agent=agent_name)
            await self._events.publish(
                AgentStateChanged(
                    agent_name=agent_name,
                    user_id=context.user_id,
                    previous_state=AgentState.THINKING.value,
                    new_state=AgentState.ERROR.value,
                )
            )
            return AgentResponse(
                agent_name=agent_name,
                content="An error occurred. I'll try again shortly.",
                data={"error": str(exc), "agent_states": self.state.agent_states},
            )

    async def execute_chain(self, user_id: UUID, steps: list[ActionStep], metadata: dict | None = None) -> list[AgentResponse]:
        results: list[AgentResponse] = []
        metadata = metadata or {}

        for step in steps:
            if step.agent_name:
                context = AgentContext(
                    user_id=user_id,
                    message=step.action,
                    metadata={**metadata, **step.parameters},
                )
                results.append(await self.invoke_agent(step.agent_name, context))
            elif step.tool_name:
                from ugra.core.tools.base import ToolName, ToolContext

                agent_name = self._state.active_agent or "orchestrator"
                agent = self._registry.get(agent_name)
                if agent and isinstance(agent, IntelligenceAgent):
                    tool_result = await agent.run_tool(step.tool_name, user_id, step.parameters)
                    results.append(
                        AgentResponse(
                            agent_name=agent_name,
                            content=tool_result.get("reasoning", "Tool executed"),
                            data=tool_result,
                        )
                    )
                else:
                    result = await self._tools.execute(
                        ToolName(step.tool_name),
                        ToolContext(user_id=user_id, agent_name="orchestrator", parameters=step.parameters),
                    )
                    results.append(
                        AgentResponse(
                            agent_name="orchestrator",
                            content=result.message,
                            data={"success": result.success, "data": result.data},
                        )
                    )
        return results

    async def plan_and_execute(self, user_id: UUID, metadata: dict | None = None) -> list[AgentResponse]:
        goal = await self._goals.get_active_goal(user_id)
        memory = await self._memory.get_or_create(user_id)
        steps_data = await self._cognition.plan_actions(
            user_id=user_id,
            goal=goal,
            memory=memory,
            available_tools=self._tools.names(),
        )

        steps = [
            ActionStep(
                tool_name=s.get("tool") if s.get("tool") else None,
                action=s.get("action", ""),
                parameters=s.get("parameters", {}),
            )
            for s in steps_data
        ]
        return await self.execute_chain(user_id, steps, metadata)

    def get_agent_state(self, agent_name: str) -> str | None:
        agent = self._registry.get(agent_name)
        if agent and isinstance(agent, IntelligenceAgent):
            return agent.state.value
        return self._state.agent_states.get(agent_name)
