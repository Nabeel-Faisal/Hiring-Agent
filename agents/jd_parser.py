import json
from models import JDRequirements
from circuit_breaker import get_breaker
from json_utils import extract_json


SYSTEM_PROMPT = """You are an expert HR analyst specialising in extracting structured requirements
from job descriptions. You always respond with valid JSON matching the required schema exactly.
Never add markdown fences or extra text — output raw JSON only."""


async def parse_jd(client, raw_text: str) -> JDRequirements:
    breaker = get_breaker("jd_parser")

    async def _call():
        text = await client.chat(
            system=SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": f"""{raw_text}

Extract all requirements from the job description above.
Return ONLY valid JSON with this exact structure:
{{
  "title": "job title",
  "department": "department name or empty string",
  "required_skills": ["skill1", "skill2"],
  "preferred_skills": ["skill1", "skill2"],
  "experience_years": 3,
  "education": "Bachelor's degree in Computer Science or equivalent",
  "responsibilities": ["responsibility1", "responsibility2"],
  "key_competencies": ["competency1", "competency2"],
  "seniority_level": "junior|mid|senior|lead|principal",
  "summary": "2-3 sentence role summary"
}}"""
            }],
            max_tokens=2000
        )
        return JDRequirements(**extract_json(text))

    return await breaker.call(_call)
