"""Tests for cover letter fallback generation."""

from ugra.application.cover_letter.fallback import build_fallback_cover_letter


def test_fallback_cover_letter_includes_job_and_company():
    letter = build_fallback_cover_letter(
        job_title="Python Developer",
        company="Acme",
        experience="5 лет опыта в backend",
        resume_content="Python FastAPI PostgreSQL Docker",
    )
    assert "Python Developer" in letter
    assert "Acme" in letter
    assert "Python" in letter


def test_fallback_cover_letter_uses_template_snippet():
    letter = build_fallback_cover_letter(
        job_title="DevOps",
        company="Cloud Inc",
        template_content="Я всегда начинаю письмо с благодарности за возможность откликнуться.",
    )
    assert "DevOps" in letter
    assert "благодарности" in letter
