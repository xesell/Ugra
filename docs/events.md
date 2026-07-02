# Событийная модель

Event-driven архитектура через `EventBus` (`core/events/bus.py`).

## Использование

```python
# Подписка
event_bus.subscribe(VacancyFound, async def handler(event: VacancyFound): ...)

# Публикация
await event_bus.publish(VacancyFound(job_id=..., user_id=..., title="...", company="..."))
```

## События

| Событие | Когда публикуется |
|---------|-------------------|
| `JobAnalyzed` | После анализа вакансии |
| `VacancyFound` | Найдена новая вакансия |
| `ApplicationSubmitted` | Отправлен отклик |
| `InterviewReceived` | Получено приглашение на интервью |
| `InterviewScheduled` | Интервью запланировано |
| `OfferReceived` | Получен оффер |
| `ResumeUpdated` | Обновлено резюме |
| `SkillGapDetected` | Обнаружен пробел в навыках |
| `LearningCompleted` | Завершено обучение |
| `NotificationSent` | Отправлено уведомление |
| `AgentStateChanged` | Изменилось состояние агента |
| `GoalProgressUpdated` | Обновлён прогресс цели |

## Правила

1. Агенты **не вызывают друг друга напрямую** — только через orchestrator или события
2. Обработчики событий не должны падать — ошибки логируются, не прерывают цепочку
3. События immutable (`frozen=True`)

## Personality + Events

```python
state = personality.react_to_event("VacancyFound")  # → EmotionalState.EXCITED
```
