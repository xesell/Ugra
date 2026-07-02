"""Agent Runtime — public API for the agents module.

Components:
    BaseAgent          — agents/base/registry.py
    CareerAgent        — agents/career/agent.py
    AgentContext       — agents/base/registry.py (transport DTO)
    UnifiedAgentContext — agents/runtime/context.py (full context)
    AgentMemory        — agents/runtime/memory.py
    AgentTools         — agents/runtime/tools.py
    AgentOrchestrator  — agents/orchestrator/intelligence_orchestrator.py
"""

from ugra.agents.base.registry import AgentContext, AgentRegistry, AgentResponse, BaseAgent
from ugra.agents.orchestrator.intelligence_orchestrator import (
    ActionStep,
    IntelligenceOrchestrator,
    OrchestratorState,
)
from ugra.agents.runtime.context import ConversationTurn, UnifiedAgentContext
from ugra.agents.runtime.context_builder import ContextBuilder
from ugra.agents.runtime.memory import AgentMemory
from ugra.agents.runtime.tools import AgentTools

# Canonical names from AI Core spec
AgentOrchestrator = IntelligenceOrchestrator

__all__ = [
    "ActionStep",
    "AgentContext",
    "AgentMemory",
    "AgentOrchestrator",
    "AgentRegistry",
    "AgentResponse",
    "AgentTools",
    "BaseAgent",
    "ContextBuilder",
    "ConversationTurn",
    "IntelligenceOrchestrator",
    "OrchestratorState",
    "UnifiedAgentContext",
]
