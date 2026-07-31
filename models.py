from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
import uuid


def gen_id() -> str:
    return str(uuid.uuid4())


class CandidateStatus(str, Enum):
    PENDING = "pending"
    SCREENING = "screening"
    SHORTLISTED = "shortlisted"
    REJECTED_SCREENING = "rejected_screening"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    INTERVIEW_IN_PROGRESS = "interview_in_progress"
    INTERVIEW_COMPLETE = "interview_complete"
    EVALUATED = "evaluated"
    SELECTED = "selected"
    REJECTED_FINAL = "rejected_final"
    EMAIL_SENT = "email_sent"


class SessionStatus(str, Enum):
    SCHEDULED = "scheduled"
    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    EXPIRED = "expired"


class JDRequirements(BaseModel):
    title: str
    department: str = ""
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    experience_years: int = 0
    education: str = ""
    responsibilities: list[str] = Field(default_factory=list)
    key_competencies: list[str] = Field(default_factory=list)
    seniority_level: str = "mid"
    summary: str = ""


class ScreeningResult(BaseModel):
    candidate_id: str
    overall_score: float = Field(ge=0.0, le=100.0)
    skill_match_score: float = Field(ge=0.0, le=100.0)
    experience_score: float = Field(ge=0.0, le=100.0)
    education_score: float = Field(ge=0.0, le=100.0)
    shortlisted: bool
    rejection_reason: Optional[str] = None
    strengths: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    summary: str = ""


class QAPair(BaseModel):
    id: str = Field(default_factory=gen_id)
    session_id: str
    question: str
    question_num: int
    answer: Optional[str] = None
    answered_at: Optional[datetime] = None


class EvaluationDimension(BaseModel):
    score: float = Field(ge=0.0, le=10.0)
    rationale: str
    evidence: list[str] = Field(default_factory=list)


class EvaluationResult(BaseModel):
    session_id: str
    technical_competency: EvaluationDimension
    communication: EvaluationDimension
    problem_solving: EvaluationDimension
    cultural_fit: EvaluationDimension
    role_alignment: EvaluationDimension
    overall_score: float = Field(ge=0.0, le=100.0)
    recommendation: str  # "STRONG_HIRE" | "HIRE" | "MAYBE" | "NO_HIRE"
    key_strengths: list[str] = Field(default_factory=list)
    concerns: list[str] = Field(default_factory=list)
    detailed_feedback: str = ""


class FeedbackInsight(BaseModel):
    question_quality_score: float = Field(ge=0.0, le=10.0)
    coverage_gaps: list[str] = Field(default_factory=list)
    suggested_improvements: list[str] = Field(default_factory=list)
    bias_flags: list[str] = Field(default_factory=list)
    summary: str = ""


class Decision(BaseModel):
    id: str = Field(default_factory=gen_id)
    session_id: str
    candidate_id: str
    ai_recommendation: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    reasoning: str = ""
    admin_decision: Optional[str] = None
    admin_notes: Optional[str] = None
    email_sent: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)


class OnboardingPlan(BaseModel):
    candidate_id: str
    recommended_start_date: str = ""
    orientation_topics: list[str] = Field(default_factory=list)
    training_plan: list[str] = Field(default_factory=list)
    mentor_requirements: list[str] = Field(default_factory=list)
    first_week_goals: list[str] = Field(default_factory=list)
    resources_needed: list[str] = Field(default_factory=list)
    summary: str = ""


# API request/response models
class JDUploadRequest(BaseModel):
    title: str
    raw_text: str


class ResumeUploadRequest(BaseModel):
    jd_id: str
    candidate_name: str
    candidate_email: str
    resume_text: str
    phone: str = ""


class AdminDecisionRequest(BaseModel):
    decision: str  # "selected" | "rejected"
    notes: Optional[str] = None


class InterviewQuestion(BaseModel):
    question: str
    category: str  # "technical" | "behavioral" | "situational" | "role_specific"
    follow_up_hint: str = ""
