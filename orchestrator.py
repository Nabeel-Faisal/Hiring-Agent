"""
State machine that drives the full hiring pipeline.
Each step is idempotent — safe to retry after failure.
"""
import json
import asyncio
from typing import Optional
from llm_client import make_client
import database as db
import audit
import email_service
from models import JDRequirements, ScreeningResult
from agents.jd_parser import parse_jd
from agents.screener import screen_resume
from agents.interviewer import generate_questions
from agents.evaluator import evaluate_interview
from agents.feedback_loop import analyse_feedback
from agents.decision_maker import make_decision
from agents.onboarding import generate_onboarding_plan




async def process_jd(jd_id: str) -> JDRequirements:
    """Parse and store JD requirements."""
    client = make_client()
    jd_row = await db.get_jd(jd_id)
    if not jd_row:
        raise ValueError(f"JD not found: {jd_id}")

    if jd_row.get("parsed_json"):
        return JDRequirements(**json.loads(jd_row["parsed_json"]))

    requirements = await parse_jd(client, jd_row["raw_text"])
    await db.update_jd_parsed(jd_id, requirements.model_dump_json())
    await audit.log_event("jd_parsed", {"jd_id": jd_id, "title": requirements.title})
    return requirements


async def process_candidate_screening(candidate_id: str) -> ScreeningResult:
    """Screen a candidate resume against the JD."""
    client = make_client()
    candidate = await db.get_candidate(candidate_id)
    if not candidate:
        raise ValueError(f"Candidate not found: {candidate_id}")

    jd = await process_jd(candidate["jd_id"])
    jd_row = await db.get_jd(candidate["jd_id"])

    await db.update_candidate_status(candidate_id, "screening")
    result = await screen_resume(
        client,
        candidate_id,
        candidate["resume_text"],
        jd,
        jd_row["raw_text"]
    )

    await db.update_candidate_screening(
        candidate_id,
        result.overall_score,
        result.model_dump_json(),
        result.shortlisted
    )

    await audit.log_event("screening_complete", {
        "candidate_id": candidate_id,
        "score": result.overall_score,
        "shortlisted": result.shortlisted
    })
    return result


async def schedule_interview(candidate_id: str) -> str:
    """Create interview session and send email invitation. Returns meeting token."""
    import secrets
    candidate = await db.get_candidate(candidate_id)
    if not candidate:
        raise ValueError(f"Candidate not found: {candidate_id}")
    if candidate.get("screening_score") is None:
        raise ValueError(f"Candidate has not been screened yet: {candidate_id}")

    # Generate unique meeting token
    token = secrets.token_urlsafe(32)
    await db.set_candidate_meeting_token(candidate_id, token)

    # Create interview session
    session_id = await db.create_interview_session(candidate_id, candidate["jd_id"])

    # Pre-generate questions
    client = make_client()
    jd = await process_jd(candidate["jd_id"])
    questions = await generate_questions(client, candidate["name"], candidate["resume_text"], jd)

    questions_data = [q.model_dump() for q in questions]
    await db.save_session_questions(session_id, questions_data)

    # Send invitation email
    try:
        email_service.send_interview_invitation(candidate["name"], candidate["email"], token)
        await audit.log_event("interview_invitation_sent", {
            "candidate_id": candidate_id,
            "session_id": session_id,
            "email": candidate["email"]
        })
    except Exception as e:
        await audit.log_event("email_error", {"candidate_id": candidate_id, "error": str(e)})

    return token


async def run_post_interview_pipeline(session_id: str) -> None:
    """Evaluate completed interview, run feedback loop, make decision."""
    session = await db.get_interview_session(session_id)
    if not session:
        raise ValueError(f"Session not found: {session_id}")

    candidate = await db.get_candidate(session["candidate_id"])
    jd = await process_jd(session["jd_id"])
    jd_row = await db.get_jd(session["jd_id"])

    qa_pairs = await db.get_qa_pairs(session_id)
    questions_meta = json.loads(session.get("questions_json") or "[]")

    # Merge category from questions_meta into qa_pairs
    merged_qa = []
    for i, pair in enumerate(qa_pairs):
        meta = questions_meta[i] if i < len(questions_meta) else {}
        merged_qa.append({**pair, "category": meta.get("category", "general")})

    client = make_client()

    # Step 1: Evaluate
    screening_row = candidate.get("screening_json")
    screening = ScreeningResult(**json.loads(screening_row)) if screening_row else None

    evaluation = await evaluate_interview(
        client, session_id, candidate["name"], candidate["resume_text"], jd, merged_qa
    )
    await db.save_evaluation(
        session_id,
        evaluation.model_dump_json(),
        evaluation.overall_score,
        evaluation.recommendation
    )
    await db.update_candidate_status(session["candidate_id"], "evaluated")
    await audit.log_event("evaluation_complete", {
        "session_id": session_id,
        "score": evaluation.overall_score,
        "recommendation": evaluation.recommendation
    })

    # Step 2: Feedback loop (non-blocking — runs in background)
    asyncio.create_task(_run_feedback(client, jd, merged_qa, evaluation.detailed_feedback, session_id))

    # Step 3: Decision
    try:
        decision_data = await make_decision(client, candidate["name"], jd, screening, evaluation)
        decision_id = await db.save_decision(
            session_id,
            session["candidate_id"],
            decision_data["recommendation"],
            decision_data.get("confidence_score", 0.5),
            decision_data.get("reasoning", "")
        )
        await audit.log_event("decision_made", {
            "session_id": session_id,
            "decision_id": decision_id,
            "recommendation": decision_data["recommendation"],
            "confidence": decision_data.get("confidence_score", 0.5)
        })
    except Exception as e:
        await audit.log_event("decision_error", {"session_id": session_id, "error": str(e)})


async def _run_feedback(client, jd, merged_qa, eval_summary, session_id):
    try:
        from agents.feedback_loop import analyse_feedback
        insight = await analyse_feedback(client, jd.title, merged_qa, eval_summary)
        await audit.log_event("feedback_insight", {
            "session_id": session_id,
            "quality_score": insight.question_quality_score,
            "bias_flags": insight.bias_flags
        })
    except Exception as e:
        await audit.log_event("feedback_error", {"session_id": session_id, "error": str(e)})


async def finalize_decision(decision_id: str, admin_decision: str, notes: Optional[str]) -> None:
    """Admin confirms/overrides decision and triggers outcome email."""
    from database import get_decision_by_session
    async with __import__("aiosqlite").connect(__import__("config").DB_PATH) as conn:
        conn.row_factory = __import__("aiosqlite").Row
        async with conn.execute(
            "SELECT * FROM decisions WHERE id=?", (decision_id,)
        ) as cur:
            row = await cur.fetchone()
            decision = dict(row) if row else None

    if not decision:
        raise ValueError(f"Decision not found: {decision_id}")

    await db.admin_update_decision(decision_id, admin_decision, notes)

    candidate = await db.get_candidate(decision["candidate_id"])
    jd_row = await db.get_jd(
        (await db.get_interview_session(decision["session_id"]))["jd_id"]
    )
    jd_title = jd_row["title"] if jd_row else "the position"

    # Update candidate status regardless of email outcome
    final_status = "selected" if admin_decision == "selected" else "rejected_final"
    await db.update_candidate_status(decision["candidate_id"], final_status)

    # Attempt to send email — log failure but never crash the endpoint
    try:
        if admin_decision == "selected":
            email_service.send_selection_email(candidate["name"], candidate["email"], jd_title)
        else:
            email_service.send_rejection_email(candidate["name"], candidate["email"], jd_title)
        await db.mark_email_sent(decision_id)
        await audit.log_event("outcome_email_sent", {
            "decision_id": decision_id,
            "candidate_id": decision["candidate_id"],
            "outcome": admin_decision
        })
    except Exception as e:
        await audit.log_event("outcome_email_error", {
            "decision_id": decision_id,
            "error": str(e),
            "note": "Decision recorded. Configure SMTP in .env to enable emails."
        })
