"""Tests for decision maker agent."""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock
from models import JDRequirements, ScreeningResult, EvaluationResult, EvaluationDimension

JD = JDRequirements(
    title="Python Engineer",
    required_skills=["Python"],
    seniority_level="mid",
    experience_years=3
)

SCREENING = ScreeningResult(
    candidate_id="c-001",
    overall_score=78.0,
    skill_match_score=85.0,
    experience_score=75.0,
    education_score=70.0,
    shortlisted=True,
    strengths=["Python", "FastAPI"],
    gaps=[]
)


def make_dim(score=7.5) -> EvaluationDimension:
    return EvaluationDimension(score=score, rationale="good", evidence=["example"])


EVALUATION = EvaluationResult(
    session_id="sess-001",
    technical_competency=make_dim(8.0),
    communication=make_dim(7.5),
    problem_solving=make_dim(7.0),
    cultural_fit=make_dim(8.0),
    role_alignment=make_dim(7.5),
    overall_score=76.0,
    recommendation="HIRE",
    key_strengths=["Python"],
    concerns=[]
)

MOCK_DECISION = {
    "recommendation": "selected",
    "confidence_score": 0.87,
    "reasoning": "Strong Python skills and solid interview performance justify selection."
}


def make_client() -> AsyncMock:
    client = AsyncMock()
    block = MagicMock()
    block.type = "text"
    block.text = json.dumps(MOCK_DECISION)
    resp = MagicMock()
    resp.content = [block]
    client.messages.create = AsyncMock(return_value=resp)
    return client


@pytest.mark.asyncio
async def test_decision_returns_dict():
    from agents.decision_maker import make_decision
    result = await make_decision(make_client(), "Alice", JD, SCREENING, EVALUATION)
    assert isinstance(result, dict)
    assert "recommendation" in result
    assert "confidence_score" in result
    assert "reasoning" in result


@pytest.mark.asyncio
async def test_decision_valid_recommendation():
    from agents.decision_maker import make_decision
    result = await make_decision(make_client(), "Alice", JD, SCREENING, EVALUATION)
    assert result["recommendation"] in ("selected", "rejected")


@pytest.mark.asyncio
async def test_decision_confidence_in_range():
    from agents.decision_maker import make_decision
    result = await make_decision(make_client(), "Alice", JD, SCREENING, EVALUATION)
    assert 0.0 <= result["confidence_score"] <= 1.0


@pytest.mark.asyncio
async def test_decision_for_rejected_candidate():
    from agents.decision_maker import make_decision
    rejected_block = MagicMock()
    rejected_block.type = "text"
    rejected_block.text = json.dumps({"recommendation": "rejected", "confidence_score": 0.72, "reasoning": "Does not meet requirements."})
    rejected_client = AsyncMock()
    rejected_resp = MagicMock()
    rejected_resp.content = [rejected_block]
    rejected_client.messages.create = AsyncMock(return_value=rejected_resp)
    result = await make_decision(rejected_client, "Bob", JD, SCREENING, EVALUATION)
    assert result["recommendation"] == "rejected"
