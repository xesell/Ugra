"""Backward-compatible LLM service facade over CompletionGateway."""

from typing import Any

from ugra.config.settings import Settings
from ugra.infrastructure.llm.completion_gateway import CompletionGateway
from ugra.infrastructure.llm.factory import create_completion_port


class LLMService:
    """Legacy interface — delegates to CompletionGateway."""

    async def generate(self, system_prompt: str, user_prompt: str) -> str: ...

    async def generate_structured(
        self, system_prompt: str, user_prompt: str, schema: dict[str, Any]
    ) -> dict[str, Any]: ...


class GatewayLLMService(LLMService):
    def __init__(self, gateway: CompletionGateway):
        self._gateway = gateway

    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        return await self._gateway.complete_text(system_prompt, user_prompt)

    async def generate_structured(
        self, system_prompt: str, user_prompt: str, schema: dict[str, Any]
    ) -> dict[str, Any]:
        return await self._gateway.complete_json(system_prompt, user_prompt, schema)


def create_llm_service(settings: Settings) -> GatewayLLMService:
    port = create_completion_port(settings)
    return GatewayLLMService(CompletionGateway(port))
