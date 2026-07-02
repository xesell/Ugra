"""LLM provider factory — swap providers without touching business logic."""

from typing import Literal

from ugra.config.settings import Settings
from ugra.infrastructure.llm.ports import LLMCompletionPort
from ugra.infrastructure.llm.providers.anthropic import AnthropicCompletionAdapter
from ugra.infrastructure.llm.providers.ollama import OllamaCompletionAdapter
from ugra.infrastructure.llm.providers.openai import OpenAICompletionAdapter

ProviderName = Literal["openai", "anthropic", "ollama"]


def create_completion_port(
    settings: Settings,
    provider: ProviderName | None = None,
    model: str | None = None,
) -> LLMCompletionPort:
    selected = provider or settings.default_llm_provider
    selected_model = model or settings.default_llm_model

    if selected == "openai":
        return OpenAICompletionAdapter(
            api_key=settings.openai_api_key,
            model=selected_model,
        )
    if selected == "anthropic":
        return AnthropicCompletionAdapter(
            api_key=settings.anthropic_api_key,
            model=selected_model,
        )
    return OllamaCompletionAdapter(
        base_url=settings.ollama_base_url,
        model=selected_model,
    )
