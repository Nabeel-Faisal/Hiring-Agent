import json
from models import JDRequirements, OnboardingPlan
from circuit_breaker import get_breaker
from json_utils import extract_json


SYSTEM_PROMPT = """You are an expert onboarding specialist creating personalised 30-day plans.
Never add markdown fences — output raw JSON only."""


async def generate_onboarding_plan(client, candidate_id: str, candidate_name: str,
                                   resume_text: str, jd: JDRequirements,
                                   evaluation_strengths: list[str],
                                   evaluation_concerns: list[str]) -> OnboardingPlan:
    breaker = get_breaker("onboarding")

    async def _call():
        text = await client.chat(
            system=SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": f"""NEW HIRE: {candidate_name}
ROLE: {jd.title} ({jd.seniority_level}) | Dept: {jd.department}
STRENGTHS: {', '.join(evaluation_strengths)}
AREAS TO DEVELOP: {', '.join(evaluation_concerns)}
RESUME: {resume_text[:800]}

Create a 30-day onboarding plan. Return ONLY valid JSON:
{{
  "candidate_id": "{candidate_id}",
  "recommended_start_date": "as soon as possible",
  "orientation_topics": ["topic1", "topic2"],
  "training_plan": ["Week 1: ...", "Week 2: ...", "Week 3: ...", "Week 4: ..."],
  "mentor_requirements": ["quality to look for"],
  "first_week_goals": ["goal1", "goal2", "goal3"],
  "resources_needed": ["resource1"],
  "summary": "2-3 sentence overview"
}}"""
            }],
            max_tokens=1500
        )
        return OnboardingPlan(**extract_json(text))

    return await breaker.call(_call)
