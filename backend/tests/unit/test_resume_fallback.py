"""Tests for resume fallback analysis."""

from ugra.application.resume.fallback_analysis import build_fallback_analysis, is_rate_limit_error


def test_is_rate_limit_error():
    assert is_rate_limit_error(Exception("429 Too Many Requests"))
    assert is_rate_limit_error(Exception("rate limit exceeded"))
    assert not is_rate_limit_error(Exception("401 Unauthorized"))


def test_build_fallback_analysis_extracts_skills():
    text = "Senior Python Developer with 7 years experience. Docker, Kubernetes, PostgreSQL."
    data = build_fallback_analysis(text)
    assert data["primary_specialization"]
    assert any(s["name"] == "Python" for s in data["skills"])
    assert len(data["ai_summary"]) >= 2
