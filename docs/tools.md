# Система инструментов

Универсальный интерфейс для действий агентов.

## Архитектура

```
IntelligenceAgent.run_tool(name, user_id, params)
        │
        ▼
ToolRegistry.execute(ToolName, ToolContext)
        │
        ▼
AgentTool.execute(context) → ToolResult
```

## Встроенные инструменты

| ToolName | Класс | Описание |
|----------|-------|----------|
| `job_search` | JobSearchTool | Поиск вакансий |
| `resume` | ResumeTool | Выбор резюме |
| `cover_letter` | CoverLetterTool | Генерация письма |
| `interview` | InterviewTool | Подготовка к интервью |
| `learning` | LearningTool | Roadmap обучения |
| `notification` | NotificationTool | Уведомления |

## Добавление инструмента

### 1. Enum

`core/tools/base.py` → `ToolName.MY_TOOL = "my_tool"`

### 2. Класс

```python
class MyTool(AgentTool):
    @property
    def name(self) -> ToolName:
        return ToolName.MY_TOOL

    async def execute(self, context: ToolContext) -> ToolResult:
        return ToolResult(
            tool_name=self.name.value,
            success=True,
            data={"result": "..."},
            reasoning="Why this tool was used",
        )
```

### 3. Регистрация

`core/tools/implementations.py` → `create_default_tool_registry()`:

```python
registry.register(MyTool(deps))
```

## ToolResult

```python
ToolResult(
    tool_name="job_search",
    success=True,
    data={"jobs": [...]},
    message="Found 15 vacancies",
    reasoning="Searched all configured job sources",  # → Cognition / UI
)
```

## Автоподключение

Инструменты регистрируются в DI через `create_default_tool_registry()`.
Orchestrator и CognitionEngine видят список через `tool_registry.names()`.
