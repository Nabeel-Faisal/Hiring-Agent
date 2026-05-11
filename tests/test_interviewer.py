"""Tests for interview question generator."""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock
from models import JDRequirements, InterviewQuestion
from config import TOTAL_QUESTIONS

JD = JDRequirements(
    title="Senior Engineer",
    required_skills=["Python", "AWS"],
    key_competencies=["leadership", "architecture"],
    experience_years=5,
    seniority_level="senior"
)

SAMPLE_QUESTIONS = [
    {"question": "Describe a complex Python system you built.", "category": "technical", "follow_up_hint": "architecture decisions"},
    {"question": "How do you handle AWS service failures?", "category": "technical", "follow_up_hint": "resilience"},
    {"question": "Tell me about a time you led a team through a difficult project.", "category": "behavioral", "follow_up_hint": "leadership"},
    {"question": "You have 2 hours to fix a production outage. Walk me through your approach.", "category": "situational", "follow_up_hint": "incident management"},
    {"question": "Why are you interested in this role specifically?", "category": "role_specific", "follow_up_hint": "motivation"},
]


def make_client(questions=None) -> AsyncMock:
    questions = questions or SAMPLE_QUESTIONS
    client = AsyncMock()
    block = MagicMock()
    block.type = "text"
    block.text = json.dumps(questions)
    resp = MagicMock()
    resp.content = [block]
    client.messages.create = AsyncMock(return_value=resp)
    return client


@pytest.mark.asyncio
async def test_generates_correct_number_of_questions():
    from agents.interviewer import generate_questions
    result = await generate_questions(make_client(), "Alice Smith", "resume text", JD)
    assert len(result) == TOTAL_QUESTIONS


@pytest.mark.asyncio
async def test_returns_interview_question_objects():
    from agents.interviewer import generate_questions
    result = await generate_questions(make_client(), "Alice Smith", "resume text", JD)
    for q in result:
        assert isinstance(q, InterviewQuestion)
        assert q.question
        assert q.category in ("technical", "behavioral", "situational", "role_specific")


@pytest.mark.asyncio
async def test_handles_extra_questions_returned(make_client=make_client):
    from agents.interviewer import generate_questions
    extra = SAMPLE_QUESTIONS * 2  # 10 items — should be truncated to TOTAL_QUESTIONS
    result = await generate_questions(make_client(extra), "Alice", "resume", JD)
    assert len(result) == TOTAL_QUESTIONS
