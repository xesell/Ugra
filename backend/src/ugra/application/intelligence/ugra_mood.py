"""Ugra mood — UI-facing state labels."""

from dataclasses import dataclass

from ugra.domain.agent_state import AgentState


@dataclass(frozen=True)
class UgraMood:
    state: AgentState
    emoji: str
    label: str
    label_en: str


MOOD_LABELS: dict[AgentState, UgraMood] = {
    AgentState.IDLE: UgraMood(AgentState.IDLE, "🐆", "Отдыхаю...", "Resting"),
    AgentState.SEARCHING: UgraMood(AgentState.SEARCHING, "🐆", "На охоте...", "Hunting"),
    AgentState.THINKING: UgraMood(AgentState.THINKING, "🐆", "Думаю...", "Thinking"),
    AgentState.WRITING: UgraMood(AgentState.WRITING, "🐆", "Готовлю письмо...", "Writing"),
    AgentState.LEARNING: UgraMood(AgentState.LEARNING, "🐆", "Изучаю вакансии...", "Learning"),
    AgentState.WAITING: UgraMood(AgentState.WAITING, "🐆", "Жду твоего решения...", "Waiting"),
    AgentState.SLEEPING: UgraMood(AgentState.SLEEPING, "🐆", "Сплю...", "Sleeping"),
    AgentState.RUNNING_TOOL: UgraMood(AgentState.RUNNING_TOOL, "🐆", "Работаю...", "Working"),
    AgentState.ERROR: UgraMood(AgentState.ERROR, "🐆", "Что-то пошло не так...", "Error"),
}


class UgraMoodService:
    """Maps machine agent state to human-readable UI labels."""

    def get_mood(self, state: AgentState | str) -> UgraMood:
        if isinstance(state, str):
            try:
                state = AgentState(state)
            except ValueError:
                return MOOD_LABELS[AgentState.IDLE]
        return MOOD_LABELS.get(state, MOOD_LABELS[AgentState.IDLE])

    def format_status(self, state: AgentState | str) -> str:
        mood = self.get_mood(state)
        return f"{mood.emoji} {mood.label}"

    def format_all(self, agent_states: dict[str, str]) -> dict[str, str]:
        return {name: self.format_status(state) for name, state in agent_states.items()}
