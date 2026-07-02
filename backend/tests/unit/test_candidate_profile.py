"""Tests for candidate profile building."""

from uuid import uuid4

from ugra.application.candidate.prompt_context import build_prompt_context
from ugra.domain.candidate_profile import (
    CandidateIdentity,
    CandidateProfile,
    ExperienceBreakdown,
    RolePriority,
    SearchStrategy,
    SpecialistLevel,
    TechSkill,
)


def test_build_prompt_context_includes_specialization_and_exclusions():
    profile = CandidateProfile(
        user_id=uuid4(),
        identity=CandidateIdentity(
            full_name="Ivan",
            primary_specialization="Senior .NET Backend Developer",
            level=SpecialistLevel.SENIOR,
            level_rationale="10+ years backend experience",
        ),
        experience=ExperienceBreakdown(total_years=12, commercial_years=10, leadership_years=3),
        skills=[
            TechSkill("C#", "Backend", 98),
            TechSkill("Docker", "Infrastructure", 90),
        ],
        domains=["FinTech", "Enterprise"],
        strengths=["architecture", "microservices"],
        weaknesses=["Frontend", "UI"],
        preferred_roles=[RolePriority("Senior .NET", "high"), RolePriority("QA", "low")],
        search_strategy=SearchStrategy(
            include_keywords=["Senior .NET", "Backend"],
            exclude_keywords=["Junior", "Frontend"],
        ),
    )
    ctx = build_prompt_context(profile)
    assert "Senior .NET Backend Developer" in ctx
    assert "C#" in ctx
    assert "Frontend" in ctx
    assert "Junior" in ctx
    assert "не анализируй PDF" in ctx
