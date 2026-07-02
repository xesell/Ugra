"""Agent lifecycle states exposed to UI and orchestration."""

from enum import StrEnum


class AgentState(StrEnum):
    IDLE = "idle"
    SEARCHING = "searching"
    THINKING = "thinking"
    WRITING = "writing"
    LEARNING = "learning"
    WAITING = "waiting"
    SLEEPING = "sleeping"
    RUNNING_TOOL = "running_tool"
    ERROR = "error"
