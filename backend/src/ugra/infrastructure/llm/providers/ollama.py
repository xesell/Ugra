"""Ollama completion adapter — transport only."""

import httpx

from ugra.infrastructure.llm.ports import LLMCompletionPort
from ugra.infrastructure.llm.types import CompletionRequest, CompletionResponse


class OllamaCompletionAdapter(LLMCompletionPort):
    def __init__(self, base_url: str, model: str):
        self._base_url = base_url.rstrip("/")
        self._model = model

    @property
    def provider_name(self) -> str:
        return "ollama"

    @property
    def model_name(self) -> str:
        return self._model

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        payload: dict = {
            "model": self._model,
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
            "stream": False,
            "options": {"temperature": request.temperature},
        }
        if request.response_format == "json":
            payload["format"] = "json"

        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(f"{self._base_url}/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()

        message = data.get("message", {})
        return CompletionResponse(
            content=str(message.get("content", "")),
            provider=self.provider_name,
            model=self._model,
            raw=data,
        )
