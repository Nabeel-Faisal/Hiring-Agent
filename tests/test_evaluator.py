"""Tests for interview evaluator agent."""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock
from models import JDRequirements, EvaluationResult, EvaluationDimension

JD = JDRequirements(
    title="Python Engineer",
    required_skills=["Python"],
    key_competencies=["problem solving"],
    experience_years=3,
    seniority_level="mid"
)

QA_PAIRS = [
    {"question": "Describe a Python project.", "answer": "I built a microservices API using FastAPI.", "category": "technical"},
    {"question": "How do you handle conflict?", "answer": "I focus on facts and propose solutions.", "category": "behavioral"},
]

MOCK_EVAL = {
    "session_id": "sess-001",
    "technical_competency": {"score": 8.5, "rationale": "Strong Python knowledge", "evidence": ["FastAPI experience"]},
    "communication": {"score": 7.0, "rationale": "Clear answers", "evidence": ["Structured responses"]},
    "problem_solving": {"score": 7.5, "rationale": "Good approach", "evidence": ["Systematic thinking"]},
    "cultural_fit": {"score": 8.0, "rationale": "Collaborative", "evidence": ["Team examples"]},
    "role_alignment": {"score": 8.0, "rationale": "Matches requirements", "evidence": ["Relevant experience"]},
    "overall_score": 79.5,
    "recommendation": "HIRE",
    "key_strengths": ["Python expertise", "Communication"],
    "concerns": [],
    "detailed_feedback": "Strong candidate who meets all core requirements."
}


def make_client() -> AsyncMock:
    client = AsyncMock()
    block = MagicMock()
    block.type = "text"
    block.text = json.dumps(MOCK_EVAL)
    resp = MagicMock()
    resp.content = [block]
    client.messages.create = AsyncMock(return_value=resp)
    return client


@pytest.mark.asyncio
async def test_evaluate_returns_result_object():
    from agents.evaluator import evaluate_interview
    result = await evaluate_interview(make_client(), "sess-001", "Alice", "resume", JD, QA_PAIRS)
    assert isinstance(result, EvaluationResult)
    assert isinstance(result.technical_competency, EvaluationDimension)
    assert result.recommendation == "HIRE"
    assert 0 <= result.overall_score <= 100


@pytest.mark.asyncio
async def test_evaluate_scores_within_range():
    from agents.evaluator import evaluate_interview
    result = await evaluate_interview(make_client(), "sess-001", "Alice", "resume", JD, QA_PAIRS)
    for dim in [result.technical_competency, result.communication, result.problem_solving,
                result.cultural_fit, result.role_alignment]:
        assert 0 <= dim.score <= 10


@pytest.mark.asyncio
async def test_evaluate_handles_no_answers():
    from agents.evaluator import evaluate_interview
    empty_qa = [{"question": "Q1", "answer": None, "category": "technical"}]
    result = await evaluate_interview(make_client(), "sess-001", "Alice", "resume", JD, empty_qa)
    assert result is not None
