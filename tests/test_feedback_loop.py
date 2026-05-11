"""Tests for feedback loop agent."""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock
from models import FeedbackInsight

QA_PAIRS = [
    {"question": "Describe a Python project.", "category": "technical"},
    {"question": "Tell me about a challenge you overcame.", "category": "behavioral"},
]

MOCK_FEEDBACK = {
    "question_quality_score": 7.5,
    "coverage_gaps": ["No system design question"],
    "suggested_improvements": ["Add architecture question"],
    "bias_flags": [],
    "summary": "Good coverage overall with minor gaps."
}


def make_client() -> AsyncMock:
    client = AsyncMock()
    block = MagicMock()
    block.type = "text"
    block.text = json.dumps(MOCK_FEEDBACK)
    resp = MagicMock()
    resp.content = [block]
    client.messages.create = AsyncMock(return_value=resp)
    return client


@pytest.mark.asyncio
async def test_feedback_returns_insight():
    from agents.feedback_loop import analyse_feedback
    result = await analyse_feedback(make_client(), "Python Engineer", QA_PAIRS, "Good candidate.")
    assert isinstance(result, FeedbackInsight)
    assert 0 <= result.question_quality_score <= 10


@pytest.mark.asyncio
async def test_feedback_detects_no_bias():
    from agents.feedback_loop import analyse_feedback
    result = await analyse_feedback(make_client(), "Python Engineer", QA_PAIRS, "Good candidate.")
    assert result.bias_flags == []


@pytest.mark.asyncio
async def test_feedback_returns_improvements():
    from agents.feedback_loop import analyse_feedback
    result = await analyse_feedback(make_client(), "Python Engineer", QA_PAIRS, "Good candidate.")
    assert len(result.suggested_improvements) > 0
