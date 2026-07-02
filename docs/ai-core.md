# AI Core

Реализация ядра AI-агента Ugra (Epic: AI Core).

## Definition of Done

| Требование | Статус | Реализация |
|------------|--------|------------|
| Agent Runtime | ✅ | `backend/src/ugra/agents/runtime/` |
| PersonalityService | ✅ | `application/intelligence/personality_service.py` |
| Agent Memory (PostgreSQL) | ✅ | `agents/runtime/memory.py` + `PostgresMemoryRepository` |
| IAgentTool + 5 tools | ✅ | `core/tools/base.py` (6 tools) |
| ILLMProvider + 3 providers | ✅ | `infrastructure/llm/ports.py` |
| Prompts as .md | ✅ | `backend/prompts/*.md` |
| Unified AgentContext | ✅ | `agents/runtime/context.py` |
| First autonomous task | ✅ | `application/autonomous/first_task.py` |
| Event subscriptions | ✅ | `application/events/handlers.py` |
| Ugra mood UI labels | ✅ | `application/intelligence/ugra_mood.py` |

## Agent Runtime (`backend/src/ugra/agents/runtime/`)

```python
from ugra.agents.runtime import (
    BaseAgent,
    AgentContext,        # transport DTO
    UnifiedAgentContext, # full context
    AgentMemory,
    AgentTools,
    AgentOrchestrator,
    ContextBuilder,
)
```

## UnifiedAgentContext

Каждый запрос собирает:

- `user_id`, `message`, `current_time`
- `current_resume`, `current_vacancy`, `current_goal`
- `memory` (LongTermMemory)
- `conversation` (история turns)
- `audience`, `communication_mode`

Сборка: `ContextBuilder.build(AgentContext)`.

## PersonalityService

```python
from ugra.application.intelligence.personality_service import PersonalityService

service = PersonalityService()
text = service.apply(response, audience=AudienceType.OWNER)
```

## Ugra Mood

```python
mood.format_status(AgentState.SEARCHING)  # "🐆 На охоте..."
```

API: `GET /api/v1/agents/mood`

## First Autonomous Task

При старте приложения (`main.py` lifespan):

1. Поиск вакансий
2. Анализ
3. Сохранение в память
4. Уведомление владельца

## PostgreSQL Memory

```env
USE_POSTGRES_MEMORY=true
DATABASE_URL=postgresql+asyncpg://ugra:ugra@localhost:5432/ugra
```

Fallback на in-memory если `USE_POSTGRES_MEMORY=false`.

## Prompts

Файлы в `backend/prompts/`:

- `career_agent.md`
- `resume_agent.md`
- `interview_agent.md`
- `cover_letter_agent.md`
- `learning_agent.md`
- `personality.md` (справочник, не для LLM)

## Архитектурные запреты

- ❌ Бизнес-логика в контроллерах
- ❌ Прямые вызовы OpenAI из сервисов
- ❌ Зависимости между агентами
- ❌ Промпты в коде
