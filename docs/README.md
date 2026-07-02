# Ugra — документация

Навигация по технической документации платформы Ugra.

## Для AI-агента

Начни с [AGENTS.md](../AGENTS.md) — правила и чеклисты для работы с репозиторием.

## Архитектура

| Документ | Содержание |
|----------|------------|
| [architecture.md](architecture.md) | Clean Architecture, слои, диаграммы |
| [intelligence-core.md](intelligence-core.md) | Ядро интеллекта (Epic 2) |
| [agents.md](agents.md) | Как создавать и регистрировать агентов |
| [personality.md](personality.md) | Personality Engine, Hunter/Professional |
| [llm-providers.md](llm-providers.md) | LLM как транспорт, провайдеры |
| [memory-and-goals.md](memory-and-goals.md) | Долговременная память и цели |
| [events.md](events.md) | Событийная модель |
| [tools.md](tools.md) | Система инструментов |
| [api.md](api.md) | REST API эндпоинты |
| [ai-core.md](ai-core.md) | AI Core (runtime, memory, autonomy) |

## Быстрые ссылки на код

| Компонент | Путь |
|-----------|------|
| Agent Runtime | `src/ugra/core/intelligence/agent_runtime.py` |
| Orchestrator | `src/ugra/agents/orchestrator/intelligence_orchestrator.py` |
| Cognition Engine | `src/ugra/application/intelligence/cognition_engine.py` |
| Personality Engine | `src/ugra/application/intelligence/personality_engine.py` |
| DI Container | `src/ugra/core/di/container.py` |
| Промпты | `prompts/` |
| Тесты | `tests/unit/` |

## Эпики

- **Epic 1** — каркас, Career Agent, Telegram, Docker
- **Epic 2** — Intelligence Core (personality, memory, goals, cognition, autonomous tasks)
