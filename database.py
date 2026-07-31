import json
import uuid
from datetime import datetime
from typing import Optional
import aiosqlite
from config import DB_PATH


async def get_db() -> aiosqlite.Connection:
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA foreign_keys=ON")
    return db


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.executescript("""
            PRAGMA journal_mode=WAL;
            PRAGMA foreign_keys=ON;

            CREATE TABLE IF NOT EXISTS jd_sessions (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                raw_text TEXT NOT NULL,
                parsed_json TEXT,
                is_published INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS candidates (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT DEFAULT '',
                resume_text TEXT NOT NULL,
                jd_id TEXT NOT NULL,
                screening_score REAL,
                screening_json TEXT,
                status TEXT DEFAULT 'pending',
                meeting_token TEXT UNIQUE,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (jd_id) REFERENCES jd_sessions(id)
            );

            CREATE TABLE IF NOT EXISTS interview_sessions (
                id TEXT PRIMARY KEY,
                candidate_id TEXT NOT NULL,
                jd_id TEXT NOT NULL,
                status TEXT DEFAULT 'scheduled',
                questions_json TEXT,
                started_at TEXT,
                ended_at TEXT,
                FOREIGN KEY (candidate_id) REFERENCES candidates(id),
                FOREIGN KEY (jd_id) REFERENCES jd_sessions(id)
            );

            CREATE TABLE IF NOT EXISTS qa_pairs (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                question TEXT NOT NULL,
                question_num INTEGER NOT NULL,
                answer TEXT,
                answered_at TEXT,
                FOREIGN KEY (session_id) REFERENCES interview_sessions(id)
            );

            CREATE TABLE IF NOT EXISTS evaluations (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                result_json TEXT NOT NULL,
                overall_score REAL,
                recommendation TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (session_id) REFERENCES interview_sessions(id)
            );

            CREATE TABLE IF NOT EXISTS decisions (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                candidate_id TEXT NOT NULL,
                ai_recommendation TEXT NOT NULL,
                confidence_score REAL,
                reasoning TEXT,
                admin_decision TEXT,
                admin_notes TEXT,
                email_sent INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now'))
            );
        """)
        await db.commit()

        # Migrate pre-existing databases that predate these columns.
        for stmt in (
            "ALTER TABLE jd_sessions ADD COLUMN is_published INTEGER DEFAULT 0",
            "ALTER TABLE candidates ADD COLUMN phone TEXT DEFAULT ''",
        ):
            try:
                await db.execute(stmt)
                await db.commit()
            except aiosqlite.OperationalError:
                pass  # column already exists


# JD helpers
async def create_jd(title: str, raw_text: str) -> str:
    jd_id = str(uuid.uuid4())
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO jd_sessions (id, title, raw_text) VALUES (?, ?, ?)",
            (jd_id, title, raw_text)
        )
        await db.commit()
    return jd_id


async def set_jd_published(jd_id: str, published: bool) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE jd_sessions SET is_published=? WHERE id=?",
            (1 if published else 0, jd_id)
        )
        await db.commit()


async def list_published_jds() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM jd_sessions WHERE is_published=1 ORDER BY created_at DESC"
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def update_jd_parsed(jd_id: str, parsed_json: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE jd_sessions SET parsed_json=? WHERE id=?",
            (parsed_json, jd_id)
        )
        await db.commit()


async def get_jd(jd_id: str) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM jd_sessions WHERE id=?", (jd_id,)) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def list_jds() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM jd_sessions ORDER BY created_at DESC") as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


# Candidate helpers
async def create_candidate(name: str, email: str, resume_text: str, jd_id: str, phone: str = "") -> str:
    cid = str(uuid.uuid4())
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO candidates (id, name, email, phone, resume_text, jd_id) VALUES (?, ?, ?, ?, ?, ?)",
            (cid, name, email, phone, resume_text, jd_id)
        )
        await db.commit()
    return cid


async def update_candidate_screening(candidate_id: str, score: float, result_json: str, shortlisted: bool) -> None:
    status = "shortlisted" if shortlisted else "rejected_screening"
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE candidates SET screening_score=?, screening_json=?, status=? WHERE id=?",
            (score, result_json, status, candidate_id)
        )
        await db.commit()


async def set_candidate_meeting_token(candidate_id: str, token: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE candidates SET meeting_token=?, status='interview_scheduled' WHERE id=?",
            (token, candidate_id)
        )
        await db.commit()


async def update_candidate_status(candidate_id: str, status: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE candidates SET status=? WHERE id=?", (status, candidate_id))
        await db.commit()


async def get_candidate(candidate_id: str) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM candidates WHERE id=?", (candidate_id,)) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def get_candidate_by_token(token: str) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM candidates WHERE meeting_token=?", (token,)) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def list_candidates(jd_id: Optional[str] = None) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if jd_id:
            async with db.execute(
                "SELECT * FROM candidates WHERE jd_id=? ORDER BY created_at DESC", (jd_id,)
            ) as cur:
                rows = await cur.fetchall()
        else:
            async with db.execute("SELECT * FROM candidates ORDER BY created_at DESC") as cur:
                rows = await cur.fetchall()
        return [dict(r) for r in rows]


# Interview session helpers
async def create_interview_session(candidate_id: str, jd_id: str) -> str:
    sid = str(uuid.uuid4())
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO interview_sessions (id, candidate_id, jd_id) VALUES (?, ?, ?)",
            (sid, candidate_id, jd_id)
        )
        await db.commit()
    return sid


async def save_session_questions(session_id: str, questions: list[dict]) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE interview_sessions SET questions_json=? WHERE id=?",
            (json.dumps(questions), session_id)
        )
        await db.commit()


async def start_interview_session(session_id: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE interview_sessions SET status='in_progress', started_at=datetime('now') WHERE id=?",
            (session_id,)
        )
        await db.commit()


async def end_interview_session(session_id: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE interview_sessions SET status='complete', ended_at=datetime('now') WHERE id=?",
            (session_id,)
        )
        await db.commit()


async def get_interview_session(session_id: str) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM interview_sessions WHERE id=?", (session_id,)) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def get_session_by_candidate(candidate_id: str) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM interview_sessions WHERE candidate_id=? ORDER BY rowid DESC LIMIT 1",
            (candidate_id,)
        ) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


# QA pair helpers
async def save_qa_pair(session_id: str, question: str, question_num: int) -> str:
    qa_id = str(uuid.uuid4())
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO qa_pairs (id, session_id, question, question_num) VALUES (?, ?, ?, ?)",
            (qa_id, session_id, question, question_num)
        )
        await db.commit()
    return qa_id


async def save_answer(qa_id: str, answer: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE qa_pairs SET answer=?, answered_at=datetime('now') WHERE id=?",
            (answer, qa_id)
        )
        await db.commit()


async def get_qa_pairs(session_id: str) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM qa_pairs WHERE session_id=? ORDER BY question_num",
            (session_id,)
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


# Evaluation helpers
async def save_evaluation(session_id: str, result_json: str, overall_score: float, recommendation: str) -> str:
    eid = str(uuid.uuid4())
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO evaluations (id, session_id, result_json, overall_score, recommendation) VALUES (?, ?, ?, ?, ?)",
            (eid, session_id, result_json, overall_score, recommendation)
        )
        await db.commit()
    return eid


async def get_evaluation(session_id: str) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM evaluations WHERE session_id=? ORDER BY rowid DESC LIMIT 1",
            (session_id,)
        ) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


# Decision helpers
async def save_decision(session_id: str, candidate_id: str, recommendation: str,
                        confidence: float, reasoning: str) -> str:
    did = str(uuid.uuid4())
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO decisions
               (id, session_id, candidate_id, ai_recommendation, confidence_score, reasoning)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (did, session_id, candidate_id, recommendation, confidence, reasoning)
        )
        await db.commit()
    return did


async def admin_update_decision(decision_id: str, admin_decision: str, notes: Optional[str]) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE decisions SET admin_decision=?, admin_notes=? WHERE id=?",
            (admin_decision, notes, decision_id)
        )
        await db.commit()


async def mark_email_sent(decision_id: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE decisions SET email_sent=1 WHERE id=?", (decision_id,))
        await db.commit()


async def get_pending_decisions() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM decisions WHERE admin_decision IS NULL ORDER BY created_at DESC"
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def get_decision_by_session(session_id: str) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM decisions WHERE session_id=? ORDER BY rowid DESC LIMIT 1",
            (session_id,)
        ) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def list_all_decisions() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM decisions ORDER BY created_at DESC") as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def delete_candidate(candidate_id: str) -> bool:
    """Delete a candidate and all their related data. Returns True if found."""
    async with aiosqlite.connect(DB_PATH) as db:
        # Fetch session IDs for this candidate
        async with db.execute(
            "SELECT id FROM interview_sessions WHERE candidate_id=?", (candidate_id,)
        ) as cur:
            session_ids = [r[0] for r in await cur.fetchall()]

        for sid in session_ids:
            await db.execute("DELETE FROM qa_pairs WHERE session_id=?", (sid,))
            await db.execute("DELETE FROM evaluations WHERE session_id=?", (sid,))
            await db.execute("DELETE FROM decisions WHERE session_id=?", (sid,))

        await db.execute("DELETE FROM interview_sessions WHERE candidate_id=?", (candidate_id,))
        cur = await db.execute("DELETE FROM candidates WHERE id=?", (candidate_id,))
        await db.commit()
        return cur.rowcount > 0


async def delete_jd(jd_id: str) -> bool:
    """Delete a JD and all related candidates and their data. Returns True if found."""
    async with aiosqlite.connect(DB_PATH) as db:
        # Get all candidates for this JD
        async with db.execute(
            "SELECT id FROM candidates WHERE jd_id=?", (jd_id,)
        ) as cur:
            candidate_ids = [r[0] for r in await cur.fetchall()]

        for cid in candidate_ids:
            async with db.execute(
                "SELECT id FROM interview_sessions WHERE candidate_id=?", (cid,)
            ) as cur:
                session_ids = [r[0] for r in await cur.fetchall()]

            for sid in session_ids:
                await db.execute("DELETE FROM qa_pairs WHERE session_id=?", (sid,))
                await db.execute("DELETE FROM evaluations WHERE session_id=?", (sid,))
                await db.execute("DELETE FROM decisions WHERE session_id=?", (sid,))

            await db.execute("DELETE FROM interview_sessions WHERE candidate_id=?", (cid,))

        await db.execute("DELETE FROM candidates WHERE jd_id=?", (jd_id,))
        cur = await db.execute("DELETE FROM jd_sessions WHERE id=?", (jd_id,))
        await db.commit()
        return cur.rowcount > 0
