"""Shared test doubles."""

from ugra.infrastructure.llm.completion_gateway import CompletionGateway


class StubGateway(CompletionGateway):
    def __init__(self):
        pass

    @property
    def provider(self) -> str:
        return "stub"

    @property
    def model(self) -> str:
        return "stub"

    async def complete_text(self, system_prompt: str, user_prompt: str, **kwargs) -> str:
        return "planned action"

    async def complete_json(self, system_prompt: str, user_prompt: str, schema, **kwargs) -> dict:
        return {
            "steps": [{"action": "search", "tool": "job_search", "rationale": "find jobs"}],
            "priority": "high",
        }
