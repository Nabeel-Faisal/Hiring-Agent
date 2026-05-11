import random
import re
from models import JDRequirements, InterviewQuestion
from circuit_breaker import get_breaker
from json_utils import extract_json
from config import TOTAL_QUESTIONS


SYSTEM_PROMPT = """You are a strict technical interviewer. Write focused, direct questions.
RULES — no exceptions:
- Each question is ONE sentence, max 25 words
- No multi-part questions ("and also", "additionally", "also tell me")
- No preamble or context — just the question itself
- Output raw JSON array only, no markdown fences"""

# ─── Easy warmup angles (Q1–Q2) ───────────────────────────────────────────────

_EASY_ANGLES = [
    "why they applied to this role specifically",
    "their strongest technical skill and one recent example using it",
    "how they prefer to learn a new technology",
    "what their typical workday looks like and how they stay productive",
    "a project they are most proud of and their specific contribution",
    "what kind of team environment brings out their best work",
    "their go-to approach when they encounter an unfamiliar bug",
    "what drew them to their current or most recent tech stack",
    "how they prioritize tasks when everything feels urgent",
    "one thing they wish they had done differently in a past project",
]

# ─── Medium angles (Q3–Q4) ────────────────────────────────────────────────────

_MEDIUM_ANGLES = [
    "a technical decision they made that they later reconsidered",
    "how they handled receiving critical feedback on their code or approach",
    "a time they had to debug a problem with no obvious starting point",
    "how they balance writing clean code with hitting deadlines",
    "a cross-team collaboration that almost fell apart and how they saved it",
    "a situation where requirements changed mid-project and how they adapted",
    "their approach to testing — what they test and what they skip",
    "a time they had to push back on a product requirement and why",
    "how they onboarded onto a new codebase and got productive fast",
    "a technical disagreement with a colleague and how it was resolved",
    "their experience with performance optimization — what the problem was and how they measured it",
    "a deployment that went wrong and exactly what they did to fix it",
]

# ─── Hard deep-dive angles (Q5) ───────────────────────────────────────────────

_HARD_ANGLES = [
    "the most complex system they designed end-to-end and the hardest trade-off they made",
    "a production incident they owned — root cause, fix, and what they changed permanently",
    "how they would design a scalable version of a core feature in their current/last product",
    "a time they inherited broken or undocumented code and had to ship from it",
    "the biggest architectural mistake they have seen or made and what the right solution was",
    "how they would approach rewriting a critical service with zero downtime",
    "a security or data integrity problem they discovered and how they resolved it",
    "a time they had to make a call with incomplete information and the outcome",
]


def _extract_resume_highlights(resume_text: str) -> list[str]:
    tech_pattern = (
        r'\b(Python|JavaScript|TypeScript|Go|Rust|Java|C\+\+|React|Vue|Angular|'
        r'Node\.js|FastAPI|Django|Flask|Spring|AWS|GCP|Azure|Kubernetes|Docker|'
        r'PostgreSQL|MySQL|MongoDB|Redis|Kafka|GraphQL|REST|gRPC|Terraform|'
        r'Git|GitHub|CI/CD|Microservices|ML|AI|LLM|Pandas|PyTorch|TensorFlow)\b'
    )
    found_techs = list(set(re.findall(tech_pattern, resume_text, re.IGNORECASE)))
    company_pattern = r'\bat\s+([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)?)\b'
    found_companies = re.findall(company_pattern, resume_text)[:3]

    highlights = []
    if found_techs:
        sample = random.sample(found_techs, min(3, len(found_techs)))
        highlights.append(f"they've used {', '.join(sample)}")
    if found_companies:
        highlights.append(f"they've worked at {found_companies[0]}")
    return highlights


async def generate_questions(client, candidate_name: str, resume_text: str,
                             jd: JDRequirements) -> list[InterviewQuestion]:
    breaker = get_breaker("interviewer")

    # Unique session seed — forces different questions even for same JD + similar resumes
    session_id = random.randint(100000, 999999)

    # Pick angles for each difficulty tier
    easy_pick       = random.sample(_EASY_ANGLES,   2)
    medium_pick     = random.sample(_MEDIUM_ANGLES, 2)
    hard_pick       = random.choice(_HARD_ANGLES)

    highlights = _extract_resume_highlights(resume_text)
    highlight_note = (
        f"Resume highlights: {'; '.join(highlights)}. Reference these where natural."
        if highlights else ""
    )

    skills_sample = (
        random.sample(jd.required_skills, min(3, len(jd.required_skills)))
        if jd.required_skills else jd.required_skills
    )

    async def _call():
        text = await client.chat(
            system=SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": f"""SESSION #{session_id} — generate a UNIQUE set of questions, different from any previous session.

ROLE: {jd.title} ({jd.seniority_level})
Key Skills: {', '.join(skills_sample)}
CANDIDATE: {candidate_name}
{highlight_note}
RESUME (excerpt):
{resume_text[:2000]}

Generate exactly {TOTAL_QUESTIONS} questions following this STRICT difficulty progression:

Q1 [EASY — max 20 words]: Ask about {easy_pick[0]}
Q2 [EASY — max 20 words]: Ask about {easy_pick[1]}
Q3 [MEDIUM — max 25 words]: Ask about {medium_pick[0]}
Q4 [MEDIUM — max 25 words]: Ask about {medium_pick[1]}
Q5 [HARD — max 30 words]: Ask about {hard_pick}

Critical rules:
- Single focused question per slot — no "and also" or multi-part questions
- Reference the candidate's actual background where natural
- Easy questions: conversational, comfortable opener — not intimidating
- Medium questions: require reflection on a real experience
- Hard question: reveals depth, judgment, and senior-level thinking
- Every question must be different from session #{session_id - 1} and all prior sessions

Return ONLY this JSON array:
[
  {{
    "question": "question text here",
    "category": "technical|behavioral|situational|role_specific",
    "follow_up_hint": "what a strong answer covers in one sentence"
  }}
]"""
            }],
            max_tokens=1500
        )
        items = extract_json(text)
        return [InterviewQuestion(**item) for item in items[:TOTAL_QUESTIONS]]

    return await breaker.call(_call)
