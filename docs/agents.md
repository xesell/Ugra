# Агенты Ugra

## Иерархия классов

```
BaseAgent (agents/base/registry.py)
    └── IntelligenceAgent (core/intelligence/agent_runtime.py)
            └── CareerAgent ✅
            └── ResumeAgent  🔜 миграция
            └── ...
```

**Новые агенты** наследуют `IntelligenceAgent`, не `BaseAgent`.

## Создание нового агента

### 1. Промпт

`prompts/my_agent/v1.yaml`:

```yaml
description: My agent system prompt
variables:
  - goal_context
  - memory_context
system: |
  You are the My Agent of Ugra.
  Current user goal: {{goal_context}}
  Memory: {{memory_context}}
```

### 2. Класс агента

`src/ugra/agents/my_agent/agent.py`:

```python
from ugra.agents.base.registry import AgentCapability, AgentResponse
from ugra.core.intelligence.agent_runtime import AgentRuntimeContext, IntelligenceAgent


class MyAgent(IntelligenceAgent):
    def __init__(self, *, personality, cognition, goal_manager, memory_repo,
                 tool_registry, prompt_manager, event_bus, llm):
        super().__init__(
            personality=personality, cognition=cognition,
            goal_manager=goal_manager, memory_repo=memory_repo,
            tool_registry=tool_registry, prompt_manager=prompt_manager,
            event_bus=event_bus,
        )
        self._llm = llm

    @property
    def name(self) -> str:
        return "my_agent"

    @property
    def capabilities(self) -> list[AgentCapability]:
        return [AgentCapability.HR]

    async def can_handle(self, context) -> float:
        return 0.9 if "keyword" in context.message.lower() else 0.1

    async def execute(self, ctx: AgentRuntimeContext) -> AgentResponse:
        system = await self.get_system_prompt(ctx.user_id)
        text = await self._llm.generate(system, ctx.message)
        return AgentResponse(agent_name=self.name, content=text)
```

### 3. Регистрация в DI

`core/di/container.py`:

```python
my_agent = providers.Singleton(
    MyAgent,
    personality=personality_engine,
    cognition=cognition_engine,
    # ... остальные intelligence deps
    llm=llm_service,
)

# В _create_agent_registry добавить my_agent
```

**Orchestrator менять не нужно.**

### 4. Тест

`tests/unit/test_my_agent.py` — can_handle, execute с mock LLM.

## AgentContext metadata

| Ключ | Тип | Описание |
|------|-----|----------|
| `channel` | str | `owner`, `hr`, `email`, `linkedin`, `hh` |
| `is_owner` | bool | Владелец → Hunter mode |
| `is_professional` | bool | Принудительный Professional |
| `skills` | list[str] | Навыки пользователя |
| `experience_years` | int | Опыт |
| `filters` | dict | Фильтры поиска |
| `autonomous` | bool | Фоновый вызов |

## AgentResponse

```python
AgentResponse(
    agent_name="career_agent",
    content="Текст для пользователя",
    data={"jobs": [...], "agent_state": "idle"},
    capabilities_used=[AgentCapability.JOB_SEARCH],
)
```

## Существующие агенты

| Агент | Класс | Статус Intelligence |
|-------|-------|---------------------|
| career_agent | CareerAgent | ✅ IntelligenceAgent |
| resume_agent | ResumeAgent | 🔜 BaseAgent |
| cover_letter_agent | CoverLetterAgent | 🔜 BaseAgent |
| interview_agent | InterviewAgent | 🔜 BaseAgent |
| learning_agent | LearningAgent | 🔜 BaseAgent |

## LangGraph

Career Agent использует LangGraph для workflow. Граф — деталь реализации агента, не ядра.
Новые агенты могут использовать LangGraph опционально через свойство `graph`.
