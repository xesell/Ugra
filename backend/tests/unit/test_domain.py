"""Tests for domain value objects."""

import pytest

from ugra.domain.value_objects import JobFilter, MatchScore


def test_match_score_valid():
    score = MatchScore(value=94.0, pros=("Kubernetes", "Docker"), cons=("Python",))
    assert score.percentage == "94%"
    assert len(score.pros) == 2


def test_match_score_invalid():
    with pytest.raises(ValueError, match="Match score must be 0-100"):
        MatchScore(value=150, pros=(), cons=())


def test_job_filter_defaults():
    f = JobFilter()
    assert f.remote_only is False
    assert f.keywords == ()
