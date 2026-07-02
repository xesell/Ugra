"""Completion gateway — Ugra's interface to LLM transport.

This is NOT the intelligence layer. It routes completion requests to the
configured provider and handles cross-cutting concerns (metrics, parsing).
All planning, memory, personality, and tool orchestration live elsewhere.
"""

import json
from typing import Any

from ugra.core.logging.setup import get_logger
from ugra.core.observability.metrics import LLM_LATENCY
from ugra.infrastructure.llm.factory import ProviderName, create_completion_port
from ugra.infrastructure.llm.ports import LLMCompletionPort
from ugra.infrastructure.llm.types import CompletionRequest, LLMMessage

logger = get_logger(__name__)


class CompletionGateway:
    """Swappable LLM gateway. Business logic must not depend on provider specifics."""

    def __init__(self, port: LLMCompletionPort):
        self._port = port

    @property
    def provider(self) -> str:
        return self._port.provider_name

    @property
    def model(self) -> str:
        return self._port.model_name

    def with_provider(self, settings, provider: ProviderName, model: str | None = None) -> "CompletionGateway":
        return CompletionGateway(create_completion_port(settings, provider, model))

    async def complete_text(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> str:
        request = CompletionRequest(
            messages=(
                LLMMessage(role="system", content=system_prompt),
                LLMMessage(role="user", content=user_prompt),
            ),
            temperature=temperature,
            max_tokens=max_tokens,
            response_format="text",
        )
        with LLM_LATENCY.labels(provider=self.provider, model=self.model).time():
            response = await self._port.complete(request)
        return response.content

    async def complete_json(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: dict[str, Any],
        *,
        temperature: float = 0.3,
    ) -> dict[str, Any]:
        schema_hint = f"\nRespond ONLY with valid JSON matching this schema:\n{json.dumps(schema)}"
        request = CompletionRequest(
            messages=(
                LLMMessage(role="system", content=system_prompt + schema_hint),
                LLMMessage(role="user", content=user_prompt),
            ),
            temperature=temperature,
            response_format="json",
        )
        with LLM_LATENCY.labels(provider=self.provider, model=self.model).time():
            response = await self._port.complete(request)
        return self._parse_json(response.content)

    @staticmethod
    def _parse_json(raw: str) -> dict[str, Any]:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(raw[start:end])
            logger.error("json_parse_failed", raw_preview=raw[:200])
            raise
