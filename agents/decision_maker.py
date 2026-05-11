import json
import re
from models import EvaluationResult, ScreeningResult, JDRequirements
from circuit_breaker import get_breaker
from json_utils import extract_json


SYSTEM_PROMPT = """You are a senior hiring manager. Output ONLY a single JSON object on one line.
No markdown, no code fences, no explanation before or after the JSON.
The entire response must be valid JSON parseable by json.loads()."""


def _extract_decision_fallback(text: str) -> dict:
    """Last-resort extraction using regex for the three known fields."""
    rec_match = re.search(r'"recommendation"\s*:\s*"(selected|rejected)"', text, re.IGNORECASE)
    conf_match = re.search(r'"confidence_score"\s*:\s*([0-9.]+)', text)
    # Grab everything between "reasoning": " and the next unescaped "
    reas_match = re.search(r'"reasoning"\s*:\s*"([\s\S]*?)"(?:\s*[,}])', text)

    if rec_match:
        return {
            "recommendation": rec_match.group(1).lower(),
            "confidence_score": float(conf_match.group(1)) if conf_match else 0.5,
            "reasoning": reas_match.group(1).replace('\n', ' ').strip() if reas_match else "",
        }
    raise ValueError(f"Cannot extract decision fields from: {text[:300]}")


async def make_decision(client, candidate_name: str, jd: JDRequirements,
                        screening: ScreeningResult, evaluation: EvaluationResult) -> dict:
    breaker = get_breaker("decision_maker")

    async def _call():
        rec = evaluation.recommendation  # STRONG_HIRE / HIRE / NO_HIRE / STRONG_NO_HIRE
        text = await client.chat(
            system=SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": (
                    f'Candidate: {candidate_name}. Role: {jd.title}. '
                    f'Screening score: {screening.overall_score}/100. '
                    f'Interview score: {evaluation.overall_score}/100. '
                    f'Interview recommendation: {rec}. '
                    f'Key strengths: {", ".join(evaluation.key_strengths[:2])}. '
                    f'Key concerns: {", ".join(evaluation.concerns[:2])}. '
                    'Respond with exactly this JSON (no newlines inside strings): '
                    '{"recommendation":"selected|rejected","confidence_score":0.0,"reasoning":"one sentence"}'
                )
            }],
            max_tokens=300
        )
        try:
            return extract_json(text)
        except ValueError:
            return _extract_decision_fallback(text)

    return await breaker.call(_call)
