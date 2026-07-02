"""Tests for learning agent skill gap analysis."""

import pytest

from ugra.agents.learning.agent import LearningAgent


class MockLLM:
    async def generate_structured(self, system_prompt, user_prompt, schema):
        return {"steps": ["Learn RAG basics", "Build a RAG pipeline"], "estimated_weeks": 3}

    async def generate(self, system_prompt, user_prompt):
        return "mock"


@pytest.mark.asyncio
async def test_analyze_gaps():
    agent = LearningAgent(MockLLM())  # type: ignore[arg-type]
    gaps = await agent.analyze_gaps(["Python", "RAG", "LangGraph"], ["Python", "Docker"])
    assert "RAG" in gaps.missing_skills
    assert "LangGraph" in gaps.missing_skills
    assert "Python" not in gaps.missing_skills


@pytest.mark.asyncio
async def test_build_roadmap():
    agent = LearningAgent(MockLLM())  # type: ignore[arg-type]
    roadmap = await agent.build_roadmap(["RAG", "LangGraph"], "middle")
    assert len(roadmap.steps) == 2
    assert roadmap.estimated_weeks == 3
