import json
from models import JDRequirements, EvaluationResult, EvaluationDimension
from circuit_breaker import get_breaker
from json_utils import extract_json
import eval_weights_loader


SYSTEM_PROMPT = """You are an expert hiring evaluator. Score interview performance objectively,
basing every score on specific evidence from the candidate's answers.
Never add markdown fences — output raw JSON only."""


async def evaluate_interview(client, session_id: str, candidate_name: str,
                             resume_text: str, jd: JDRequirements,
                             qa_pairs: list[dict]) -> EvaluationResult:
    breaker = get_breaker("evaluator")
    weights = eval_weights_loader.load()

    qa_text = "\n\n".join(
        f"Q{i+1} [{pair.get('category', 'general')}]: {pair['question']}\n"
        f"A{i+1}: {pair.get('answer', '[no answer provided]')}"
        for i, pair in enumerate(qa_pairs)
    )

    async def _call():
        text = await client.chat(
            system=SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": f"""ROLE: {jd.title} ({jd.seniority_level})
Required Skills: {', '.join(jd.required_skills)}

CANDIDATE: {candidate_name}
RESUME: {resume_text[:1000]}

INTERVIEW TRANSCRIPT:
{qa_text}

WEIGHTS: technical={weights['technical_competency']*100:.0f}% communication={weights['communication']*100:.0f}% problem_solving={weights['problem_solving']*100:.0f}% cultural_fit={weights['cultural_fit']*100:.0f}% role_alignment={weights['role_alignment']*100:.0f}%

Score each dimension 0-10 with evidence from answers.
Overall = weighted sum × 10. Recommendation: STRONG_HIRE(85+) HIRE(70-84) MAYBE(55-69) NO_HIRE(<55)

Return ONLY valid JSON:
{{
  "session_id": "{session_id}",
  "technical_competency": {{"score": <0-10>, "rationale": "...", "evidence": ["..."]}},
  "communication": {{"score": <0-10>, "rationale": "...", "evidence": ["..."]}},
  "problem_solving": {{"score": <0-10>, "rationale": "...", "evidence": ["..."]}},
  "cultural_fit": {{"score": <0-10>, "rationale": "...", "evidence": ["..."]}},
  "role_alignment": {{"score": <0-10>, "rationale": "...", "evidence": ["..."]}},
  "overall_score": <0-100>,
  "recommendation": "STRONG_HIRE|HIRE|MAYBE|NO_HIRE",
  "key_strengths": ["..."],
  "concerns": ["..."],
  "detailed_feedback": "paragraph of comprehensive feedback"
}}"""
            }],
            max_tokens=2500
        )
        data = extract_json(text)
        for dim in ["technical_competency", "communication", "problem_solving", "cultural_fit", "role_alignment"]:
            data[dim] = EvaluationDimension(**data[dim])
        return EvaluationResult(**data)

    return await breaker.call(_call)
