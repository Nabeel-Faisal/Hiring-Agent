"""Tests for resume screener agent."""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock
from models import JDRequirements, ScreeningResult


JD = JDRequirements(
    title="Python Engineer",
    required_skills=["Python", "FastAPI"],
    experience_years=3,
    seniority_level="mid",
    summary="Mid-level Python backend role"
)

STRONG_RESULT = {
    "candidate_id": "abc-123",
    "overall_score": 82.0,
    "skill_match_score": 90.0,
    "experience_score": 85.0,
    "education_score": 75.0,
    "shortlisted": True,
    "rejection_reason": None,
    "strengths": ["Strong Python", "FastAPI experience"],
    "gaps": [],
    "summary": "Strong candidate with all required skills."
}

WEAK_RESULT = {
    "candidate_id": "xyz-456",
    "overall_score": 42.0,
    "skill_match_score": 30.0,
    "experience_score": 50.0,
    "education_score": 60.0,
    "shortlisted": False,
    "rejection_reason": "Missing core required skills",
    "strengths": ["Motivated"],
    "gaps": ["No Python experience", "No FastAPI"],
    "summary": "Does not meet minimum requirements."
}


def make_client(response_data: dict) -> AsyncMock:
    client = AsyncMock()
    block = MagicMock()
    block.type = "text"
    block.text = json.dumps(response_data)
    resp = MagicMock()
    resp.content = [block]
    client.messages.create = AsyncMock(return_value=resp)
    return client


@pytest.mark.asyncio
async def test_screen_shortlists_strong_candidate():
    from agents.screener import screen_resume
    result = await screen_resume(make_client(STRONG_RESULT), "abc-123", "5 years Python…", JD, "raw jd")
    assert isinstance(result, ScreeningResult)
    assert result.shortlisted is True
    assert result.overall_score >= 60


@pytest.mark.asyncio
async def test_screen_rejects_weak_candidate():
    from agents.screener import screen_resume
    result = await screen_resume(make_client(WEAK_RESULT), "xyz-456", "1 year Java…", JD, "raw jd")
    assert result.shortlisted is False
    assert result.rejection_reason is not None


@pytest.mark.asyncio
async def test_screen_uses_cache_control(make_client=make_client):
    from agents.screener import screen_resume
    client = make_client(STRONG_RESULT)
    await screen_resume(client, "abc-123", "resume", JD, "raw jd")
    call_args = client.messages.create.call_args
    kwargs = call_args.kwargs if call_args.kwargs else call_args[1]
    messages = kwargs.get("messages", [])
    user_content = messages[0]["content"]
    assert any(b.get("cache_control") == {"type": "ephemeral"} for b in user_content)
