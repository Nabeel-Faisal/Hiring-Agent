"""Tests for JD parser agent."""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from models import JDRequirements


SAMPLE_JD = """
Senior Python Backend Engineer

We are looking for a Senior Python Backend Engineer with 5+ years experience.

Requirements:
- Python, FastAPI, PostgreSQL, Redis
- Experience with microservices and Docker
- Bachelor's in Computer Science or related field

Responsibilities:
- Design and build RESTful APIs
- Mentor junior engineers
- Participate in architecture decisions

Nice to have: Kubernetes, AWS, GraphQL
"""

MOCK_RESPONSE = {
    "title": "Senior Python Backend Engineer",
    "department": "Engineering",
    "required_skills": ["Python", "FastAPI", "PostgreSQL", "Redis"],
    "preferred_skills": ["Kubernetes", "AWS", "GraphQL"],
    "experience_years": 5,
    "education": "Bachelor's in Computer Science or related field",
    "responsibilities": ["Design and build RESTful APIs", "Mentor junior engineers"],
    "key_competencies": ["microservices", "Docker"],
    "seniority_level": "senior",
    "summary": "Senior backend role focused on Python and API development."
}


@pytest.fixture
def mock_client():
    client = AsyncMock()
    content_block = MagicMock()
    content_block.type = "text"
    content_block.text = json.dumps(MOCK_RESPONSE)
    response = MagicMock()
    response.content = [content_block]
    client.messages.create = AsyncMock(return_value=response)
    return client


@pytest.mark.asyncio
async def test_parse_jd_returns_requirements(mock_client):
    from agents.jd_parser import parse_jd
    result = await parse_jd(mock_client, SAMPLE_JD)
    assert isinstance(result, JDRequirements)
    assert result.title == "Senior Python Backend Engineer"
    assert "Python" in result.required_skills
    assert result.experience_years == 5
    assert result.seniority_level == "senior"


@pytest.mark.asyncio
async def test_parse_jd_strips_markdown_fences(mock_client):
    from agents.jd_parser import parse_jd
    content_block = MagicMock()
    content_block.type = "text"
    content_block.text = f"```json\n{json.dumps(MOCK_RESPONSE)}\n```"
    mock_client.messages.create.return_value.content = [content_block]

    result = await parse_jd(mock_client, SAMPLE_JD)
    assert result.title == "Senior Python Backend Engineer"


@pytest.mark.asyncio
async def test_parse_jd_calls_api_with_cache_control(mock_client):
    from agents.jd_parser import parse_jd
    await parse_jd(mock_client, SAMPLE_JD)

    call_args = mock_client.messages.create.call_args
    messages = call_args.kwargs.get("messages") or call_args.args[0] if call_args.args else []
    if not messages:
        messages = call_args[1].get("messages", [])
    user_msg = messages[0]
    content = user_msg["content"]
    first_block = content[0]
    assert first_block.get("cache_control") == {"type": "ephemeral"}


@pytest.mark.asyncio
async def test_parse_jd_circuit_breaker_trips_on_repeated_failure():
    from agents.jd_parser import parse_jd
    from circuit_breaker import get_breaker, CBState

    breaker = get_breaker("jd_parser")
    breaker._failures = 0
    breaker._state = breaker._state.__class__.CLOSED

    fail_client = AsyncMock()
    fail_client.messages.create = AsyncMock(side_effect=RuntimeError("API down"))

    for _ in range(3):
        try:
            await parse_jd(fail_client, "test")
        except Exception:
            pass

    assert breaker.state == CBState.OPEN
