import json
from models import JDRequirements, ScreeningResult
from circuit_breaker import get_breaker
from json_utils import extract_json


SYSTEM_PROMPT = """You are a senior technical recruiter. You objectively evaluate candidates against
job requirements and return structured JSON assessments. Be fair, evidence-based, and concise.
Never add markdown fences — output raw JSON only."""


async def screen_resume(client, candidate_id: str, resume_text: str,
                        jd: JDRequirements, jd_raw: str) -> ScreeningResult:
    breaker = get_breaker("screener")

    jd_context = f"""JOB REQUIREMENTS:
Title: {jd.title} | Seniority: {jd.seniority_level} | Experience: {jd.experience_years}+ years
Required Skills: {', '.join(jd.required_skills)}
Preferred Skills: {', '.join(jd.preferred_skills)}
Education: {jd.education}
Key Competencies: {', '.join(jd.key_competencies)}"""

    async def _call():
        text = await client.chat(
            system=SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": f"""{jd_context}

CANDIDATE RESUME:
{resume_text}

Evaluate this candidate. Return ONLY valid JSON:
{{
  "candidate_id": "{candidate_id}",
  "overall_score": <0-100>,
  "skill_match_score": <0-100>,
  "experience_score": <0-100>,
  "education_score": <0-100>,
  "shortlisted": <true if overall_score >= 60, else false>,
  "rejection_reason": "<reason if not shortlisted, else null>",
  "strengths": ["strength1", "strength2"],
  "gaps": ["gap1", "gap2"],
  "summary": "2-3 sentence assessment"
}}"""
            }],
            max_tokens=1500
        )
        return ScreeningResult(**extract_json(text))

    return await breaker.call(_call)
