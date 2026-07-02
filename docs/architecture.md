# Архитектура Ugra

## Обзор

Ugra построена на **Clean Architecture** с event-driven элементами и plugin-based агентами.

```
┌─────────────────────────────────────────────────────────────────┐
│                      Presentation Layer                          │
│              FastAPI (routes)  │  Telegram Bot                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                      Application Layer                             │
│   Use Cases  │  CognitionEngine  │  GoalManager  │  Scheduler    │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                        Domain Layer                                │
│  Entities  │  Memory  │  Goals  │  Events  │  Repository Ports   │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                     Infrastructure Layer                           │
│  PostgreSQL  │  LLM Adapters  │  Job Sources  │  RAG  │  MCP     │
└─────────────────────────────────────────────────────────────────┘
```

## Принцип разделения интеллекта и LLM

```
┌──────────────────────────────────────┐
│         Ugra Intelligence Core        │
│                                       │
│  CognitionEngine    — планирование    │
│  GoalManager        — цели            │
│  PersonalityEngine  — стиль речи      │
│  MemoryRepository   — долгая память   │
│  ToolRegistry       — инструменты     │
│  EventBus           — события         │
│  AgentState         — состояние UI    │
└──────────────┬───────────────────────┘
               │ CompletionGateway (port)
    ┌──────────┼──────────┐
    ▼          ▼          ▼
  OpenAI   Anthropic   Ollama
```

LLM используется **только** для генерации текста/JSON по запросу CognitionEngine или агентов.
Планирование, фильтрация вакансий, выбор резюме, игнор компаний — **детерминированная логика Ugra**.

## Слои

### Domain (`backend/src/ugra/domain/`)

Чистая бизнес-логика без внешних зависимостей.

- `entities/` — UserProfile, JobVacancy, Resume
- `memory.py` — LongTermMemory и связанные сущности
- `goals.py` — Goal, GoalStatus, GoalType
- `agent_state.py` — AgentState enum
- `reasoning.py` — ReasoningRecord
- `personality.py` — CommunicationMode, AudienceType
- `events/` — доменные события
- `repositories/` — ABC-порты (интерфейсы)

### Application (`backend/src/ugra/application/`)

Оркестрация use cases и intelligence-модулей.

- `use_cases/` — SearchJobs, RouteMessage, AnalyzeJob
- `intelligence/` — CognitionEngine, GoalManager, PersonalityEngine
- `autonomous/` — AutonomousScheduler

### Core (`backend/src/ugra/core/`)

Инфраструктура платформы.

- `di/container.py` — Dependency Injection
- `events/bus.py` — EventBus
- `tools/` — ToolRegistry, AgentTool
- `intelligence/agent_runtime.py` — IntelligenceAgent base class
- `logging/`, `observability/` — structlog, OTEL, Prometheus

### Infrastructure (`backend/src/ugra/infrastructure/`)

Внешние системы.

- `llm/` — порты и адаптеры провайдеров (httpx, не LangChain в ядре)
- `backend/prompts/` — PromptManager
- `persistence/` — SQLAlchemy, репозитории
- `adapters/job_sources/` — HH, Habr, GeekJob
- `rag/` — pgvector knowledge base
- `mcp/` — MCP registry

### Agents (`backend/src/ugra/agents/`)

Тонкие модули — делегируют intelligence core.

- `base/registry.py` — BaseAgent, AgentRegistry
- `orchestrator/` — IntelligenceOrchestrator
- `career/`, `resume/`, `cover_letter/`, `interview/`, `learning/`

### Presentation (`backend/src/ugra/presentation/`)

- `api/routes.py` — REST API
- `telegram/bot.py` — Telegram UI

## Plugin-based агенты

```
AgentRegistry
    ├── career_agent      (IntelligenceAgent)
    ├── resume_agent      (BaseAgent → миграция)
    ├── cover_letter_agent
    ├── interview_agent
    └── learning_agent
         │
         ▼
IntelligenceOrchestrator.route(context)
    → can_handle() scoring
    → invoke() best agent
```

Новый агент = новый файл + регистрация в `Container`. Orchestrator не меняется.

## Dependency Injection

Все зависимости собираются в `Container` (`core/di/container.py`):

```python
container.orchestrator()
container.cognition_engine()
container.personality_engine()
container.goal_manager()
container.memory_repository()
container.tool_registry()
container.career_agent()
```

## Конфигурация

Через `.env` / `config/settings.py`:

- `DATABASE_URL` — PostgreSQL
- `DEFAULT_LLM_PROVIDER` — openai | anthropic | ollama
- `AUTONOMOUS_ENABLED` — фоновые задачи агента
- `TELEGRAM_BOT_TOKEN`

## Observability

- **structlog** — структурированное логирование
- **OpenTelemetry** — трейсинг (production)
- **Prometheus** — метрики (`AGENT_INVOCATIONS`, `LLM_LATENCY`)

## Тестирование

```
backend/tests/unit/
├── test_domain.py
├── test_orchestrator.py
├── test_intelligence_core.py
└── test_learning_agent.py
```

Запуск: `pytest backend/tests/unit -q`
