"""LLM ports — Ugra defines what it needs; providers implement transport only."""

from abc import ABC, abstractmethod

from ugra.infrastructure.llm.types import CompletionRequest, CompletionResponse


class LLMCompletionPort(ABC):
    """Transport port for text completion. Intelligence lives in Ugra, not here."""

    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @property
    @abstractmethod
    def model_name(self) -> str: ...

    @abstractmethod
    async def complete(self, request: CompletionRequest) -> CompletionResponse: ...

    async def health_check(self) -> bool:
        try:
            from ugra.infrastructure.llm.types import LLMMessage

            response = await self.complete(
                CompletionRequest(
                    messages=(LLMMessage(role="user", content="ping"),),
                    max_tokens=5,
                    temperature=0.0,
                )
            )
            return bool(response.content)
        except Exception:
            return False


# Canonical interface name from AI Core spec
ILLMProvider = LLMCompletionPort
