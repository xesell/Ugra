# LLM Providers

## Принцип

LLM — **заменяемый транспорт**. Ugra определяет интерфейс, провайдеры его реализуют.

```
CognitionEngine / Agents
        │
        ▼
CompletionGateway        ← единая точка входа
        │
        ▼
LLMCompletionPort (ABC)  ← порт
        │
   ┌────┼────┐
   ▼    ▼    ▼
OpenAI Anthropic Ollama  ← адаптеры (httpx)
```

## Файлы

| Файл | Роль |
|------|------|
| `infrastructure/llm/ports.py` | `LLMCompletionPort` ABC |
| `infrastructure/llm/types.py` | `CompletionRequest`, `CompletionResponse` |
| `infrastructure/llm/completion_gateway.py` | `CompletionGateway` — метрики, JSON parsing |
| `infrastructure/llm/factory.py` | `create_completion_port()` |
| `infrastructure/llm/providers/openai.py` | OpenAI adapter |
| `infrastructure/llm/providers/anthropic.py` | Anthropic adapter |
| `infrastructure/llm/providers/ollama.py` | Ollama adapter |
| `infrastructure/llm/service.py` | `GatewayLLMService` — legacy facade |

## Конфигурация

```env
DEFAULT_LLM_PROVIDER=openai    # openai | anthropic | ollama
DEFAULT_LLM_MODEL=gpt-4o-mini
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
OLLAMA_BASE_URL=http://localhost:11434
```

## Использование

### Через Gateway (предпочтительно)

```python
text = await gateway.complete_text(system_prompt, user_prompt)
data = await gateway.complete_json(system_prompt, user_prompt, schema)
```

### Через Legacy Service (существующие агенты)

```python
text = await llm_service.generate(system_prompt, user_prompt)
data = await llm_service.generate_structured(system_prompt, user_prompt, schema)
```

## Смена провайдера

```python
gateway.with_provider(settings, provider="anthropic", model="claude-sonnet-4-20250514")
```

Бизнес-логика не меняется.

## Добавление нового провайдера

1. Создать `infrastructure/llm/providers/my_provider.py`:

```python
class MyProviderAdapter(LLMCompletionPort):
    @property
    def provider_name(self) -> str:
        return "my_provider"

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        # HTTP call to provider API
        ...
```

2. Добавить в `factory.py`
3. Добавить в `Settings.default_llm_provider` Literal
4. Тест с mock HTTP

## Что запрещено

- Импорт LangChain в domain/application
- Прямые вызовы OpenAI SDK из агентов
- Бизнес-логика (if match > 60) в промптах
- Хардкод API keys

## Метрики

`LLM_LATENCY` (Prometheus) — labels: `provider`, `model`
