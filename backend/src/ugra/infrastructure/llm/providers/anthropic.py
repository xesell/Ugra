"""Anthropic completion adapter — transport only."""

import httpx

from ugra.infrastructure.llm.ports import LLMCompletionPort
from ugra.infrastructure.llm.types import CompletionRequest, CompletionResponse, TokenUsage


class AnthropicCompletionAdapter(LLMCompletionPort):
    def __init__(self, api_key: str, model: str, base_url: str = "https://api.anthropic.com"):
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")

    @property
    def provider_name(self) -> str:
        return "anthropic"

    @property
    def model_name(self) -> str:
        return self._model

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        system_parts = [m.content for m in request.messages if m.role == "system"]
        messages = [{"role": m.role, "content": m.content} for m in request.messages if m.role != "system"]

        payload: dict = {
            "model": self._model,
            "max_tokens": request.max_tokens or 4096,
            "messages": messages,
            "temperature": request.temperature,
        }
        if system_parts:
            payload["system"] = "\n\n".join(system_parts)

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self._base_url}/v1/messages",
                headers={
                    "x-api-key": self._api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        content_blocks = data.get("content", [])
        text = "".join(block.get("text", "") for block in content_blocks if block.get("type") == "text")
        usage_data = data.get("usage", {})
        usage = TokenUsage(
            prompt_tokens=usage_data.get("input_tokens", 0),
            completion_tokens=usage_data.get("output_tokens", 0),
            total_tokens=usage_data.get("input_tokens", 0) + usage_data.get("output_tokens", 0),
        )
        return CompletionResponse(
            content=text,
            provider=self.provider_name,
            model=self._model,
            usage=usage,
            raw=data,
        )
