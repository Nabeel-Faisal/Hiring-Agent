import json
from models import FeedbackInsight
from circuit_breaker import get_breaker
from json_utils import extract_json


SYSTEM_PROMPT = """You are an expert in interview process quality assurance.
Never add markdown fences — output raw JSON only."""


async def analyse_feedback(client, jd_title: str, qa_pairs: list[dict],
                           evaluation_summary: str) -> FeedbackInsight:
    breaker = get_breaker("feedback_loop")

    qa_text = "\n".join(
        f"Q{i+1} [{pair.get('category','?')}]: {pair['question']}"
        for i, pair in enumerate(qa_pairs)
    )

    async def _call():
        text = await client.chat(
            system=SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": f"""ROLE: {jd_title}
QUESTIONS: {qa_text}
EVALUATION: {evaluation_summary}

Analyse interview quality. Return ONLY valid JSON:
{{
  "question_quality_score": <0-10>,
  "coverage_gaps": ["area not covered"],
  "suggested_improvements": ["specific suggestion"],
  "bias_flags": ["any biased/discriminatory patterns"],
  "summary": "2-3 sentence assessment"
}}"""
            }],
            max_tokens=1000
        )
        return FeedbackInsight(**extract_json(text))

    return await breaker.call(_call)
