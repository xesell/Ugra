"""Versioned prompt storage — prompts live outside source code as .md or .yaml."""

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from ugra.core.logging.setup import get_logger

logger = get_logger(__name__)

DEFAULT_PROMPTS_DIR = Path(__file__).resolve().parents[4] / "prompts"

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)", re.DOTALL)


@dataclass(frozen=True)
class PromptTemplate:
    agent: str
    version: str
    system: str
    description: str = ""
    variables: tuple[str, ...] = ()


class PromptManager:
    """Loads agent prompts from external .md or .yaml files."""

    def __init__(self, prompts_dir: Path | None = None):
        self._dir = prompts_dir or DEFAULT_PROMPTS_DIR
        self._cache: dict[str, PromptTemplate] = {}

    def load(self, agent: str, version: str = "v1") -> PromptTemplate:
        key = f"{agent}:{version}"
        if key in self._cache:
            return self._cache[key]

        template = self._load_md(agent) or self._load_yaml(agent, version) or self._fallback(agent, version)
        self._cache[key] = template
        return template

    def _load_md(self, agent: str) -> PromptTemplate | None:
        path = self._dir / f"{agent}.md"
        if not path.exists():
            return None

        raw = path.read_text(encoding="utf-8")
        meta: dict = {}
        body = raw

        match = _FRONTMATTER_RE.match(raw)
        if match:
            meta = yaml.safe_load(match.group(1)) or {}
            body = match.group(2).strip()

        return PromptTemplate(
            agent=agent,
            version="md",
            system=body,
            description=meta.get("description", ""),
            variables=tuple(meta.get("variables", [])),
        )

    def _load_yaml(self, agent: str, version: str) -> PromptTemplate | None:
        path = self._dir / agent / f"{version}.yaml"
        if not path.exists():
            return None

        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return PromptTemplate(
            agent=agent,
            version=version,
            system=data.get("system", ""),
            description=data.get("description", ""),
            variables=tuple(data.get("variables", [])),
        )

    def _fallback(self, agent: str, version: str) -> PromptTemplate:
        logger.warning("prompt_not_found", agent=agent, version=version, dir=str(self._dir))
        return PromptTemplate(
            agent=agent,
            version=version,
            system=f"You are the {agent} agent for Ugra platform.",
        )

    def render(self, agent: str, version: str = "v1", **variables: str) -> str:
        template = self.load(agent, version)
        rendered = template.system
        for key, value in variables.items():
            rendered = rendered.replace(f"{{{{{key}}}}}", value)
        return rendered

    def list_versions(self, agent: str) -> list[str]:
        versions = []
        if (self._dir / f"{agent}.md").exists():
            versions.append("md")
        agent_dir = self._dir / agent
        if agent_dir.exists():
            versions.extend(sorted(p.stem for p in agent_dir.glob("*.yaml")))
        return versions
