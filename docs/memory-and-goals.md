# Память и цели

## Long-Term Memory

Агрегат `LongTermMemory` (`domain/memory.py`) — всё, что Ugra знает о пользователе.

### Сущности

| Сущность | Описание |
|----------|----------|
| `UserPreferences` | Предпочтения (роли, зарплата, remote) |
| `resume_ids` | Ссылки на версии резюме |
| `vacancy_history` | История вакансий |
| `interview_history` | История интервью |
| `offer_history` | История офферов |
| `communication_history` | История общения |
| `favorite_companies` | Любимые компании |
| `ignored_companies` | Игнорируемые компании |
| `learned_technologies` | Изученные технологии |
| `recommendations` | Полученные рекомендации |
| `rejection_reasons` | Причины отказов |

### Repository

```python
memory = await memory_repo.get_or_create(user_id)
memory.ignored_companies.append(CompanyPreference(company="BadCorp", reason="toxic"))
await memory_repo.save(memory)
```

### Реализации

| Класс | Назначение |
|-------|------------|
| `InMemoryMemoryRepository` | Dev / тесты (текущий default в DI) |
| `PostgresMemoryRepository` | Production (таблица `long_term_memory`) |

### API

`GET /api/v1/memory/{user_id}` — сводка памяти.

## Goal System

Каждая работа агента выравнивается с активной целью.

### Типы целей (`GoalType`)

| Тип | Пример |
|-----|--------|
| `find_job` | Получить работу AI Engineer |
| `salary_increase` | Зарплата выше текущей |
| `interview_prep` | Подготовиться к интервью |
| `learn_skill` | Изучить RAG |
| `custom` | Произвольная цель |

### Goal Manager

```python
goal = await goal_manager.set_goal(user_id, "Get AI Engineer job", GoalType.FIND_JOB)
active = await goal_manager.get_active_goal(user_id)
aligned = await goal_manager.align_action(user_id, "search vacancies")  # True/False
await goal_manager.update_progress(goal.id, user_id, 0.5)
```

### Правила

- Только **одна активная цель** на пользователя
- Новая цель → предыдущая ставится `paused`
- `align_action()` проверяет соответствие действия типу цели

### API

```
POST /api/v1/goals
GET  /api/v1/goals/{user_id}
```

### События

- `GoalProgressUpdated` — при изменении progress

## Связь памяти, целей и cognition

```python
# В IntelligenceAgent.invoke()
goal = await self._goals.get_active_goal(user_id)
memory = await self._memory.get_or_create(user_id)

# Cognition использует оба
should_apply, rationale = cognition.evaluate_vacancy_fit(user_id, job, memory, goal)
steps = await cognition.plan_actions(user_id, goal, memory, tools)
```

## PostgreSQL модели

`infrastructure/persistence/models/memory.py`:

- `MemoryModel` — JSON blob `data_json`
- `GoalModel` — отдельная таблица `goals`

Миграция на production: заменить `InMemoryGoalRepository` / `InMemoryMemoryRepository` на Postgres-реализации в `Container`.
