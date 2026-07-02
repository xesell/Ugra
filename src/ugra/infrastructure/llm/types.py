"""LLM transport types — provider-agnostic data contracts."""

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass(frozen=True)
class LLMMessage:
    role: Literal["system", "user", "assistant"]
    content: str


@dataclass(frozen=True)
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass(frozen=True)
class CompletionRequest:
    messages: tuple[LLMMessage, ...]
    temperature: float = 0.7
    max_tokens: int | None = None
    response_format: Literal["text", "json"] = "text"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CompletionResponse:
    content: str
    provider: str
    model: str
    usage: TokenUsage | None = None
    raw: dict[str, Any] = field(default_factory=dict)
