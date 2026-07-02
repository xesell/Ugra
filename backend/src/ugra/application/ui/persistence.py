"""File-backed persistence for UI state (cover letters, resumes, applications)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from ugra.config.settings import get_settings
from ugra.core.logging.setup import get_logger

logger = get_logger(__name__)


def _project_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "pyproject.toml").exists():
            return parent
    return Path.cwd()


def resolve_data_path(relative: str) -> Path:
    path = Path(relative)
    if path.is_absolute():
        return path
    return _project_root() / path


def load_ui_state(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("ui_state_load_failed", path=str(path), error=str(exc))
        return None


def save_ui_state(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def default_ui_state_path() -> Path:
    settings = get_settings()
    canonical = resolve_data_path(settings.ui_state_path)
    if canonical.exists():
        return canonical
    legacy = Path.cwd() / settings.ui_state_path
    if legacy.exists() and legacy.resolve() != canonical.resolve():
        canonical.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(legacy, canonical)
        logger.info("ui_state_migrated", from_path=str(legacy), to_path=str(canonical))
    return canonical
