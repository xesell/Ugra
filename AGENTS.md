# AGENTS.md — правила для AI-агента в репозитории Ugra

Этот файл — **источник истины** для любого AI-агента (Cursor, CI-бот, автоматизации), работающего с кодом Ugra.
Перед изменениями читай `docs/` и следуй правилам ниже.

## Миссия проекта

Ugra — production-ready платформа персональных AI-агентов для профессионального развития.
MVP: **Career Agent** (поиск работы, резюме, интервью, обучение).

**Ugra — не чат-обёртка над LLM.** Интеллект (планирование, память, личность, цели, инструменты, состояние) принадлежит платформе. LLM — заменяемый транспорт.

## Обязательное чтение

| Документ | Когда читать |
|----------|--------------|
| [docs/README.md](docs/README.md) | Навигация по документации |
| [docs/architecture.md](docs/architecture.md) | Любые архитектурные изменения |
| [docs/intelligence-core.md](docs/intelligence-core.md) | Агенты, orchestrator, cognition |
| [docs/agents.md](docs/agents.md) | Добавление/изменение агентов |
| [docs/personality.md](docs/personality.md) | Стиль общения Ugra |
| [docs/llm-providers.md](docs/llm-providers.md) | Работа с LLM |
| [docs/ai-core.md](docs/ai-core.md) | AI Core — runtime, memory, autonomy |

## Жёсткие правила (NEVER)

1. **Не делать тонкий слой над OpenAI API.** Вся логика — в `CognitionEngine`, `GoalManager`, `PersonalityEngine`, а не в промптах.
2. **Не класть личность в system prompt.** Hunter/Professional — только через `PersonalityEngine`.
3. **Не менять orchestrator/registry** при добавлении нового агента — только регистрация в DI.
4. **Не хардкодить промпты** в `.py` — только `prompts/{agent}/v{N}.yaml` + `PromptManager`.
5. **Не импортировать LangChain** в domain/application слоях.
6. **Не ломать Clean Architecture:** domain не зависит от infrastructure.
7. **Не коммитить** `.env`, API-ключи, токены.
8. **Не создавать коммиты** без явной просьбы пользователя.

## Обязательные практики (ALWAYS)

1. **Новые агенты** наследуют `IntelligenceAgent` (`core/intelligence/agent_runtime.py`), не `BaseAgent` напрямую.
2. **Новые инструменты** — класс `AgentTool` + регистрация в `ToolRegistry`, не inline-логика в агенте.
3. **Решения агента** сопровождай записью в `CognitionEngine` (`ReasoningRecord`).
4. **События** публикуй через `EventBus`, не прямые вызовы между агентами.
5. **Состояние агента** меняй через `_set_state()` — UI читает `AgentState`.
6. **DI** — все зависимости через `Container` в `core/di/container.py`.
7. **Тесты** — добавляй unit-тесты для новой бизнес-логики в `tests/unit/`.
8. **Минимальный diff** — не рефактори несвязанный код.

## Слои и куда класть код

```
src/ugra/
├── domain/          # Сущности, value objects, порты репозиториев, события
├── application/     # Use cases, intelligence (cognition, goals, personality)
├── core/            # DI, events, tools, agent runtime
├── infrastructure/  # DB, LLM adapters, prompts, RAG, внешние API
├── agents/          # Конкретные агенты (тонкий слой над runtime)
└── presentation/    # FastAPI, Telegram
```

| Что добавляешь | Куда |
|----------------|------|
| Новая сущность памяти | `domain/memory.py` + repository port |
| Новое доменное событие | `domain/events/__init__.py` |
| Бизнес-правило выбора вакансии | `application/intelligence/cognition_engine.py` |
| Новый LLM-провайдер | `infrastructure/llm/providers/` + `factory.py` |
| [docs/memory-and-goals.md](docs/memory-and-goals.md) | Память и цели |

| Промпт агента | `prompts/{agent_name}.md` (предпочтительно) или `prompts/{agent}/v{N}.yaml` |
| Правило стиля речи | `application/intelligence/personality_engine.py` |

## Personality — краткая памятка

| Режим | Аудитория | Поведение |
|-------|-----------|-----------|
| **Hunter** | Владелец приложения | Снежный барс, охотничья лексика, лёгкий юмор |
| **Professional** | HR, email, LinkedIn, HH | От лица пользователя, без AI и звериных фраз |

**Профессионализм всегда выше юмора.**

## Чеклист перед PR / завершением задачи

- [ ] Код в правильном слое Clean Architecture
- [ ] Промпты в YAML, не в коде
- [ ] Личность не в system prompt
- [ ] Reasoning записан для нетривиальных решений
- [ ] События опубликованы где уместно
- [ ] Агент зарегистрирован в DI, orchestrator не тронут
- [ ] `pytest tests/unit` проходит
- [ ] Документация в `docs/` обновлена при изменении архитектуры

## Команды разработки

```bash
# Тесты
pytest tests/unit -q

# API
uvicorn ugra.main:app --reload

# Telegram bot
python -m ugra.presentation.telegram.bot

# Линтер
ruff check src tests
```

## История эпиков

| Эпик | Статус | Описание |
|------|--------|----------|
| Epic 1 | ✅ | Каркас платформы, Career Agent MVP, Docker, Telegram |
| Epic 2 | ✅ | Intelligence Core — personality, memory, goals, tools, cognition |
| AI Core | ✅ | Agent runtime, PersonalityService, PostgreSQL memory, autonomy, mood UI |
| Epic 3+ | 🔜 | Миграция остальных агентов на IntelligenceAgent |

## Обновление этого файла

При добавлении нового правила или эпика — обновляй `AGENTS.md` и соответствующий документ в `docs/`.
Правила в `.cursor/rules/` должны оставаться синхронизированы с этим файлом.
