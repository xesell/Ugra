"""Tests for UI state path resolution."""

from pathlib import Path

from ugra.application.ui.persistence import resolve_data_path


def test_resolve_data_path_uses_project_root():
    path = resolve_data_path("data/ui_state.json")
    assert path.is_absolute()
    assert path.name == "ui_state.json"
    assert path.parent.name == "data"
    assert (path.parent.parent / "pyproject.toml").exists()
