"""Agent Orchestrator — backward-compatible alias."""

from ugra.agents.orchestrator.intelligence_orchestrator import (
    ActionStep,
    IntelligenceOrchestrator,
    OrchestratorState,
)

# Backward compatibility
AgentOrchestrator = IntelligenceOrchestrator

__all__ = [
    "ActionStep",
    "AgentOrchestrator",
    "IntelligenceOrchestrator",
    "OrchestratorState",
]
