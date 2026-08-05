import os
from dotenv import load_dotenv

load_dotenv()

# Anthropic (optional)
ANTHROPIC_API_KEY: str = os.environ.get("ANTHROPIC_API_KEY", "")
MODEL: str = "claude-opus-4-7"

# Groq (free — https://console.groq.com)
GROQ_API_KEY: str = os.environ.get("GROQ_API_KEY", "")
MODEL_GROQ: str = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

# Database
DB_PATH: str = os.environ.get("DB_PATH", "interview_system.db")
AUDIT_LOG_PATH: str = os.environ.get("AUDIT_LOG_PATH", "audit.jsonl")

# Email (SendGrid HTTPS API — SMTP ports are blocked on Render's free tier)
SENDGRID_API_KEY: str = os.environ.get("SENDGRID_API_KEY", "")
EMAIL_FROM: str = os.environ.get("EMAIL_FROM", "")
COMPANY_NAME: str = os.environ.get("COMPANY_NAME", "HiringCo")

# Server
HOST: str = os.environ.get("HOST", "0.0.0.0")
PORT: int = int(os.environ.get("PORT", "8000"))
BASE_URL: str = os.environ.get("BASE_URL", f"http://localhost:{PORT}")

# Screening thresholds
SCREENING_PASS_SCORE: float = float(os.environ.get("SCREENING_PASS_SCORE", "60.0"))

# Interview
INTERVIEW_DURATION_SECONDS: int = int(os.environ.get("INTERVIEW_DURATION_SECONDS", "600"))  # 10 min
TOTAL_QUESTIONS: int = int(os.environ.get("TOTAL_QUESTIONS", "5"))
ANSWER_TIMEOUT_SECONDS: int = int(os.environ.get("ANSWER_TIMEOUT_SECONDS", "120"))  # 2 min per question

# Circuit breaker
CB_FAILURE_THRESHOLD: int = 3
CB_RESET_TIMEOUT_SECONDS: int = 60

# ChromaDB
CHROMA_PATH: str = os.environ.get("CHROMA_PATH", "chroma_db")
