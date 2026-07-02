"""Domain value objects."""

from dataclasses import dataclass


@dataclass(frozen=True)
class MatchScore:
    value: float
    pros: tuple[str, ...]
    cons: tuple[str, ...]

    def __post_init__(self) -> None:
        if not 0 <= self.value <= 100:
            msg = f"Match score must be 0-100, got {self.value}"
            raise ValueError(msg)

    @property
    def percentage(self) -> str:
        return f"{self.value:.0f}%"


@dataclass(frozen=True)
class JobFilter:
    country: str | None = None
    remote_only: bool = False
    salary_min: int | None = None
    technologies: tuple[str, ...] = ()
    level: str | None = None
    keywords: tuple[str, ...] = ()
    sources: tuple[str, ...] = ()
