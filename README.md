# HireAI — Automated Hiring Agent

An end-to-end AI-powered hiring system that screens resumes, conducts live voice interviews, evaluates candidates, and sends decision emails — all autonomously.

Built with **FastAPI**, **Groq (Llama 3.3 70B)**, and a fully custom dark-theme dashboard.

---

## Features

- **Public Careers Page** — Candidates browse open positions at `/jobs`, read the full JD, and apply themselves with name, email, phone, and resume — no HR data entry required
- **Staged Hiring Pipeline** — Applications land unscreened; HR explicitly moves each candidate through Applications → Screening → Interview → Decision, with a human checkpoint at every stage
- **Resume Screening** — AI scores and ranks each candidate against the job description on demand (bulk "Send to Screening" from the dashboard)
- **AI Interview System** — Generates unique, difficulty-progressed questions per candidate and conducts them via a real-time chat or voice interface
- **Voice Interview Mode** — AI speaks questions aloud via browser TTS; candidate answers by microphone with live speech-to-text transcription
- **Screen + Camera Monitoring** — Requires camera, microphone, and screen sharing to maintain interview integrity
- **Automated Emails** — Sends professional HTML interview invitations, selection, and rejection emails via Gmail SMTP
- **Admin Dashboard** — Full sidebar-based dark dashboard covering Job Descriptions (with Publish/Draft control), Applications, Screening, Interview, and Decisions
- **Decision Engine** — AI evaluates interview answers and scores candidates; admin reviews and sends final hire/reject emails in one click
- **Unique Questions Per Candidate** — Every interview session generates a fresh, personalized question set with a random seed — no repeated questions even for the same role
- **Question Difficulty Progression** — Q1–Q2 easy warmup, Q3–Q4 medium, Q5 hard deep-dive

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.9+, FastAPI, Uvicorn |
| AI / LLM | Groq API — Llama 3.3 70B Versatile (free tier) |
| Database | SQLite via aiosqlite |
| Embeddings | ChromaDB |
| Email | Gmail SMTP with App Passwords |
| Frontend | Vanilla JS, CSS custom properties (dark design system) |
| Real-time | WebSockets |
| SSL | Auto-generated self-signed cert (for LAN HTTPS) |

---

## Project Structure

```
interview_system/
├── agents/
│   ├── interviewer.py       # Question generation with difficulty progression
│   ├── screener.py          # Resume scoring against JD
│   ├── evaluator.py         # Interview answer evaluation
│   ├── decision_maker.py    # Final hire/reject decision
│   ├── jd_parser.py         # Parse job descriptions into structured data
│   ├── onboarding.py        # Candidate onboarding flow
│   └── feedback_loop.py     # Feedback and improvement loop
├── static/
│   ├── index.html           # Admin dashboard
│   ├── jobs.html             # Public careers page — list of open positions
│   ├── job-detail.html       # Public JD page + apply form
│   ├── interview.html       # Candidate interview room
│   ├── css/
│   │   ├── style.css         # Full dark design system (shared)
│   │   └── public.css        # Careers page layout
│   └── js/
│       ├── admin.js         # Dashboard logic
│       ├── public.js         # Careers page + apply form logic
│       └── interview.js     # Interview + voice mode logic
├── api.py                   # FastAPI routes and WebSocket handler
├── database.py              # SQLite models and queries
├── email_service.py         # HTML email templates
├── orchestrator.py          # Interview session orchestration
├── models.py                # Pydantic data models
├── config.py                # Environment config
├── run.py                   # Dual HTTP+HTTPS server launcher
├── requirements.txt
└── .env.example
```

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/Nabeel-Faisal/Hiring-Agent.git
cd Hiring-Agent
```

### 2. Install dependencies

```bash
pip3 install -r requirements.txt
```

### 3. Configure environment

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

```env
# Groq API (free at console.groq.com)
GROQ_API_KEY=gsk_your_key_here
GROQ_MODEL=llama-3.3-70b-versatile

# Email — Gmail with App Password (enable 2FA first)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx
EMAIL_FROM=your@gmail.com
COMPANY_NAME=Your Company Name

# Server
HOST=0.0.0.0
PORT=8000
BASE_URL=https://YOUR_LAN_IP:8443

# Thresholds
SCREENING_PASS_SCORE=60.0
INTERVIEW_DURATION_SECONDS=600
TOTAL_QUESTIONS=5
```

> **Gmail App Password**: Go to Google Account → Security → 2-Step Verification → App Passwords → generate one for "Mail".

> **BASE_URL**: Set this to your machine's LAN IP with port 8443 (e.g. `https://192.168.1.100:8443`). This is the URL sent in invitation emails so candidates can access the HTTPS interview room.

### 4. Run the server

```bash
python3 run.py
```

This starts two servers simultaneously:
- **HTTP on :8000** — Admin dashboard (localhost only)
- **HTTPS on :8443** — Candidate interview room (LAN accessible, camera/mic requires HTTPS)

An SSL certificate is auto-generated on first run. Candidates will see a browser security warning on first visit — they should click **Advanced → Proceed**.

---

## Usage

### Admin Workflow

1. Open **http://localhost:8000** in your browser
2. Go to **Job Descriptions** → paste a JD, let it parse, then click **Publish** to make it visible on the public careers page (new JDs start as Draft)
3. Candidates apply themselves via `/jobs` (see Candidate Workflow below) — or add one manually from the **Applications** tab
4. Go to **Applications** → select candidates with the checkboxes → **Send to Screening**
5. Go to **Screening** → review the AI score for each candidate → click **Send Interview Invite** (available for every screened candidate, pass or fail — the AI score is guidance, the call is always yours)
6. Go to **Interview** → track Pending / Complete status; open a candidate's details to see their evaluation once complete
7. Go to **Decisions** → review AI evaluation scores → click Select or Reject to send the final email

### Candidate Workflow

1. Candidate visits `/jobs`, browses open positions, and opens one to read the full description
2. Clicks **Apply for this role** (available at the top and bottom of the JD) → fills in name, email, phone, and uploads a resume
3. Receives an interview invitation email once HR screens and approves the application, with a unique HTTPS link
4. Opens link → grants camera, microphone, and screen share permissions
5. Optionally enables **Voice Interview Mode** (AI speaks, candidate answers by voice)
6. Clicks **Start Interview →**
7. Answers 5 questions (2 easy → 2 medium → 1 hard) within the time limit
8. Receives selection or rejection email after admin decision

---

## Interview Question System

Questions are generated fresh for every candidate session using a random session seed. For the same job description, no two candidates will receive the same set.

**Difficulty tiers:**

| Question | Level | Word Limit | Style |
|---|---|---|---|
| Q1 | Easy | 20 words | Warmup — comfortable opener |
| Q2 | Easy | 20 words | Simple behavioral |
| Q3 | Medium | 25 words | Requires real experience |
| Q4 | Medium | 25 words | Situational / technical |
| Q5 | Hard | 30 words | Deep judgment, senior thinking |

---

## Voice Interview Mode

- **Text-to-Speech**: AI reads each question aloud using the browser's `SpeechSynthesis` API (prefers Neural/Google voices)
- **Speech-to-Text**: Candidate answers are transcribed in real time using `SpeechRecognition` (Chrome / Edge only)
- **Interrupt support**: Candidate can tap the mic button at any time to stop the AI and start answering
- Falls back gracefully to text mode if voice APIs are unavailable

> Voice mode requires Chrome or Edge on HTTPS. Firefox does not support `SpeechRecognition`.

---

## Environment Variables Reference

| Variable | Description | Default |
|---|---|---|
| `GROQ_API_KEY` | Groq API key | required |
| `GROQ_MODEL` | LLM model name | `llama-3.3-70b-versatile` |
| `SMTP_HOST` | SMTP server | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP port | `587` |
| `SMTP_USER` | Email address | required |
| `SMTP_PASSWORD` | Gmail App Password | required |
| `EMAIL_FROM` | From address in emails | required |
| `COMPANY_NAME` | Shown in emails | required |
| `HOST` | Server bind address | `0.0.0.0` |
| `PORT` | HTTP port (admin) | `8000` |
| `BASE_URL` | HTTPS URL for invite links | required |
| `SCREENING_PASS_SCORE` | Score threshold for the Shortlisted/Rejected badge shown to HR (guidance only — HR can send an interview invite regardless) | `60.0` |
| `INTERVIEW_DURATION_SECONDS` | Interview time limit | `600` |
| `TOTAL_QUESTIONS` | Number of interview questions | `5` |
| `DB_PATH` | SQLite database file | `interview_system.db` |
| `CHROMA_PATH` | ChromaDB storage path | `chroma_db` |

---

## Requirements

```
fastapi
uvicorn[standard]
groq
aiosqlite
chromadb
python-multipart
python-dotenv
aiosmtplib
cryptography
pydantic
pypdf2
python-docx
```

---

## License

MIT
