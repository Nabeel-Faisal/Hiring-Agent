"""
FastAPI application — REST endpoints + WebSocket interview room.
"""
import asyncio
import json
import secrets
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

import database as db
import orchestrator
import file_parser
from models import (
    JDUploadRequest, ResumeUploadRequest, AdminDecisionRequest
)
from config import INTERVIEW_DURATION_SECONDS, TOTAL_QUESTIONS


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.init_db()
    yield


app = FastAPI(title="AI Interview System", version="1.0.0", lifespan=lifespan)

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ─── Admin dashboard ───────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def serve_admin():
    return (STATIC_DIR / "index.html").read_text()


@app.get("/jobs", response_class=HTMLResponse)
async def serve_jobs_list():
    return (STATIC_DIR / "jobs.html").read_text()


@app.get("/jobs/{jd_id}", response_class=HTMLResponse)
async def serve_job_detail(jd_id: str):
    return (STATIC_DIR / "job-detail.html").read_text()


@app.get("/interview/{token}", response_class=HTMLResponse)
async def serve_interview_room(token: str):
    candidate = await db.get_candidate_by_token(token)
    if not candidate:
        raise HTTPException(status_code=404, detail="Invalid interview link")
    if candidate["status"] not in ("interview_scheduled", "interview_in_progress"):
        return HTMLResponse("<h2>This interview link has already been used or expired.</h2>", status_code=410)
    return (STATIC_DIR / "interview.html").read_text()


# ─── JD endpoints ──────────────────────────────────────────────────────────────

@app.post("/api/jd")
async def upload_jd(body: JDUploadRequest):
    jd_id = await db.create_jd(body.title, body.raw_text)
    asyncio.create_task(_bg_parse_jd(jd_id))
    return {"jd_id": jd_id, "message": "Job description received — parsing in background"}


async def _bg_parse_jd(jd_id: str):
    try:
        await orchestrator.process_jd(jd_id)
    except Exception as e:
        import audit
        await audit.log_event("jd_parse_error", {"jd_id": jd_id, "error": str(e)})


@app.get("/api/jd")
async def list_jds():
    rows = await db.list_jds()
    return rows


@app.get("/api/jd/{jd_id}")
async def get_jd(jd_id: str):
    row = await db.get_jd(jd_id)
    if not row:
        raise HTTPException(404, "JD not found")
    return row


@app.delete("/api/jd/{jd_id}")
async def delete_jd(jd_id: str):
    found = await db.delete_jd(jd_id)
    if not found:
        raise HTTPException(404, "JD not found")
    return {"message": "Job description and all related candidates deleted"}


@app.post("/api/jd/{jd_id}/publish")
async def publish_jd(jd_id: str, body: dict):
    jd_row = await db.get_jd(jd_id)
    if not jd_row:
        raise HTTPException(404, "JD not found")
    published = bool(body.get("published"))
    await db.set_jd_published(jd_id, published)
    return {"message": "Published" if published else "Unpublished"}


@app.post("/api/jd/upload")
async def upload_jd_file(
    title: str = Form(...),
    file: UploadFile = File(...)
):
    content = await file.read()
    try:
        raw_text = file_parser.extract_text(file.filename, content)
    except ValueError as e:
        raise HTTPException(400, str(e))
    if not raw_text.strip():
        raise HTTPException(400, "Could not extract text from the file. Try a different format.")
    jd_id = await db.create_jd(title, raw_text)
    asyncio.create_task(_bg_parse_jd(jd_id))
    return {"jd_id": jd_id, "message": "Job description received — parsing in background"}


# ─── Candidate / Resume endpoints ──────────────────────────────────────────────

@app.post("/api/resume")
async def upload_resume(body: ResumeUploadRequest):
    jd_row = await db.get_jd(body.jd_id)
    if not jd_row:
        raise HTTPException(404, "JD not found")
    candidate_id = await db.create_candidate(
        body.candidate_name, body.candidate_email, body.resume_text, body.jd_id, body.phone
    )
    return {"candidate_id": candidate_id, "message": "Application received — send to screening when ready"}


@app.post("/api/resume/upload")
async def upload_resume_file(
    jd_id: str = Form(...),
    candidate_name: str = Form(...),
    candidate_email: str = Form(...),
    phone: str = Form(""),
    file: UploadFile = File(...)
):
    jd_row = await db.get_jd(jd_id)
    if not jd_row:
        raise HTTPException(404, "JD not found")
    content = await file.read()
    try:
        resume_text = file_parser.extract_text(file.filename, content)
    except ValueError as e:
        raise HTTPException(400, str(e))
    if not resume_text.strip():
        raise HTTPException(400, "Could not extract text from the resume file.")
    candidate_id = await db.create_candidate(candidate_name, candidate_email, resume_text, jd_id, phone)
    return {"candidate_id": candidate_id, "message": "Application received — send to screening when ready"}


@app.post("/api/candidates/screen")
async def bulk_send_to_screening(body: dict):
    candidate_ids = body.get("candidate_ids") or []
    queued = 0
    for cid in candidate_ids:
        candidate = await db.get_candidate(cid)
        if not candidate or candidate["status"] != "pending":
            continue
        asyncio.create_task(_bg_screen(cid))
        queued += 1
    return {"queued": queued, "message": f"{queued} candidate(s) sent to screening"}


async def _bg_screen(candidate_id: str):
    try:
        await orchestrator.process_candidate_screening(candidate_id)
    except Exception as e:
        import audit
        await db.update_candidate_status(candidate_id, "pending")
        await audit.log_event("screening_error", {"candidate_id": candidate_id, "error": str(e)})


@app.get("/api/candidates")
async def list_candidates(jd_id: Optional[str] = None):
    return await db.list_candidates(jd_id)


@app.delete("/api/candidates/{candidate_id}")
async def delete_candidate(candidate_id: str):
    found = await db.delete_candidate(candidate_id)
    if not found:
        raise HTTPException(404, "Candidate not found")
    return {"message": "Candidate and all related data deleted"}


@app.get("/api/candidates/{candidate_id}")
async def get_candidate(candidate_id: str):
    row = await db.get_candidate(candidate_id)
    if not row:
        raise HTTPException(404, "Candidate not found")
    evaluation = await db.get_evaluation(
        (await db.get_session_by_candidate(candidate_id) or {}).get("id", "")
    )
    decision = None
    session = await db.get_session_by_candidate(candidate_id)
    if session:
        decision = await db.get_decision_by_session(session["id"])
    return {**row, "evaluation": evaluation, "decision": decision}


# ─── Public careers site ────────────────────────────────────────────────────────

@app.get("/api/public/jobs")
async def public_list_jobs():
    return await db.list_published_jds()


@app.get("/api/public/jobs/{jd_id}")
async def public_get_job(jd_id: str):
    jd_row = await db.get_jd(jd_id)
    if not jd_row or not jd_row.get("is_published"):
        raise HTTPException(404, "This job is not currently accepting applications")
    return jd_row


@app.post("/api/public/apply")
async def public_apply(
    jd_id: str = Form(...),
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(""),
    file: UploadFile = File(...)
):
    jd_row = await db.get_jd(jd_id)
    if not jd_row or not jd_row.get("is_published"):
        raise HTTPException(404, "This job is not currently accepting applications")
    content = await file.read()
    try:
        resume_text = file_parser.extract_text(file.filename, content)
    except ValueError as e:
        raise HTTPException(400, str(e))
    if not resume_text.strip():
        raise HTTPException(400, "Could not extract text from the resume file.")
    candidate_id = await db.create_candidate(name, email, resume_text, jd_id, phone)
    return {"candidate_id": candidate_id, "message": "Application received"}


# ─── Interview scheduling ───────────────────────────────────────────────────────

@app.post("/api/candidates/{candidate_id}/schedule")
async def schedule_interview(candidate_id: str):
    candidate = await db.get_candidate(candidate_id)
    if not candidate:
        raise HTTPException(404, "Candidate not found")
    if candidate.get("screening_score") is None:
        raise HTTPException(400, "Candidate has not been screened yet")
    token = await orchestrator.schedule_interview(candidate_id)
    return {"token": token, "message": "Interview scheduled and invitation sent"}


# ─── Admin decision endpoints ───────────────────────────────────────────────────

@app.get("/api/decisions")
async def list_decisions():
    return await db.list_all_decisions()


@app.get("/api/decisions/pending")
async def pending_decisions():
    return await db.get_pending_decisions()


@app.post("/api/decisions/{decision_id}")
async def admin_decide(decision_id: str, body: AdminDecisionRequest):
    if body.decision not in ("selected", "rejected"):
        raise HTTPException(400, "decision must be 'selected' or 'rejected'")
    try:
        await orchestrator.finalize_decision(decision_id, body.decision, body.notes)
    except ValueError as e:
        raise HTTPException(404, str(e))
    from config import SMTP_USER
    email_note = "" if SMTP_USER and SMTP_USER != "your@gmail.com" else " (Email not sent — configure SMTP in .env)"
    return {"message": f"Decision recorded{email_note}"}


@app.get("/api/decisions/{session_id}/session")
async def get_decision_by_session(session_id: str):
    row = await db.get_decision_by_session(session_id)
    if not row:
        raise HTTPException(404, "Decision not found")
    return row


# ─── WebSocket interview room ───────────────────────────────────────────────────

@app.websocket("/ws/interview/{token}")
async def interview_ws(websocket: WebSocket, token: str):
    await websocket.accept()
    candidate = await db.get_candidate_by_token(token)
    if not candidate:
        await websocket.send_json({"type": "error", "message": "Invalid interview token"})
        await websocket.close()
        return

    if candidate["status"] not in ("interview_scheduled", "interview_in_progress"):
        await websocket.send_json({"type": "error", "message": "Interview already completed or expired"})
        await websocket.close()
        return

    session = await db.get_session_by_candidate(candidate["id"])
    if not session:
        await websocket.send_json({"type": "error", "message": "No interview session found"})
        await websocket.close()
        return

    session_id = session["id"]
    questions_data = json.loads(session.get("questions_json") or "[]")

    if not questions_data:
        await websocket.send_json({"type": "error", "message": "Interview questions not ready yet. Please try again in a moment."})
        await websocket.close()
        return

    await db.start_interview_session(session_id)
    await db.update_candidate_status(candidate["id"], "interview_in_progress")

    start_time = time.time()

    await websocket.send_json({
        "type": "welcome",
        "message": f"Welcome, {candidate['name']}! Your interview is starting.",
        "total_questions": len(questions_data),
        "duration_seconds": INTERVIEW_DURATION_SECONDS
    })

    # Brief pause to let the candidate settle
    await asyncio.sleep(2)

    qa_ids = []

    for i, q_data in enumerate(questions_data):
        elapsed = time.time() - start_time
        remaining = INTERVIEW_DURATION_SECONDS - elapsed
        if remaining < 30:
            await websocket.send_json({
                "type": "time_up",
                "message": "Time limit reached. Thank you for your responses."
            })
            break

        # Store question in DB
        qa_id = await db.save_qa_pair(session_id, q_data["question"], i + 1)
        qa_ids.append(qa_id)

        await websocket.send_json({
            "type": "question",
            "question_num": i + 1,
            "total": len(questions_data),
            "text": q_data["question"],
            "category": q_data.get("category", "general"),
            "remaining_seconds": int(remaining)
        })

        # Wait for answer with timeout
        answer = None
        try:
            answer_timeout = min(120, remaining - 10)  # 2 min per question max
            data = await asyncio.wait_for(websocket.receive_json(), timeout=answer_timeout)
            if data.get("type") == "answer":
                answer = data.get("text", "").strip()
        except asyncio.TimeoutError:
            await websocket.send_json({
                "type": "timeout",
                "message": "Time for this question has passed. Moving on."
            })
        except WebSocketDisconnect:
            break

        if answer:
            await db.save_answer(qa_id, answer)
            await websocket.send_json({"type": "ack", "message": "Response recorded."})

    # End of interview
    await db.end_interview_session(session_id)
    await db.update_candidate_status(candidate["id"], "interview_complete")

    await websocket.send_json({
        "type": "interview_end",
        "message": "Thank you for completing your interview. We will be in touch with our decision soon."
    })

    # Trigger post-interview pipeline in background
    asyncio.create_task(orchestrator.run_post_interview_pipeline(session_id))

    try:
        await websocket.close()
    except Exception:
        pass
