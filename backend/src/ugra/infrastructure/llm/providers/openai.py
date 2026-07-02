"""OpenAI completion adapter — transport only."""

import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from ugra.infrastructure.llm.ports import LLMCompletionPort
from ugra.infrastructure.llm.types import CompletionRequest, CompletionResponse, LLMMessage, TokenUsage


def _is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in (429, 500, 502, 503, 504)
    return isinstance(exc, httpx.TransportError)


class OpenAICompletionAdapter(LLMCompletionPort):
    def __init__(self, api_key: str, model: str, base_url: str = "https://api.openai.com/v1"):
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def model_name(self) -> str:
        return self._model

    @retry(
        retry=retry_if_exception(_is_retryable),
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=2, min=2, max=30),
        reraise=True,
    )
    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        payload: dict = {
            "model": self._model,
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
            "temperature": request.temperature,
        }
        if request.max_tokens is not None:
            payload["max_tokens"] = request.max_tokens
        if request.response_format == "json":
            payload["response_format"] = {"type": "json_object"}

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self._base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        choice = data["choices"][0]["message"]["content"]
        usage_data = data.get("usage", {})
        usage = TokenUsage(
            prompt_tokens=usage_data.get("prompt_tokens", 0),
            completion_tokens=usage_data.get("completion_tokens", 0),
            total_tokens=usage_data.get("total_tokens", 0),
        )
        return CompletionResponse(
            content=str(choice),
            provider=self.provider_name,
            model=self._model,
            usage=usage,
            raw=data,
        )
