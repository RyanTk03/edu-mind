"""QCM-related Pydantic schemas for API request/response."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.qcm import QCMDifficulty, QCMStatus


# ── Options ────────────────────────────────────────────────────────────────────

class QCMOptionSchema(BaseModel):
    label: str
    text : str


# ── Question (no correct answer exposed to student) ───────────────────────────

class QCMQuestionSchema(BaseModel):
    order        : int
    question_text: str
    options      : list[QCMOptionSchema]
    # correct_answer is intentionally hidden from this schema
    student_answer: Optional[str]  = None
    is_correct    : Optional[bool] = None
    score         : Optional[float]= None
    feedback      : Optional[str]  = None
    gap_analysis  : Optional[str]  = None

    class Config:
        from_attributes = True


class QCMQuestionWithAnswerSchema(QCMQuestionSchema):
    """Extends question schema to include correct answer (shown after evaluation)."""
    correct_answer: str
    explanation   : str = ""


# ── Grade Report ───────────────────────────────────────────────────────────────

class QCMGradeReportSchema(BaseModel):
    total_score    : float
    correct_count  : int
    total_questions: int
    grade_letter   : str
    grade_label    : str
    strong_points  : list[str]
    weak_points    : list[str]
    recommendations: list[str]
    summary        : str

    class Config:
        from_attributes = True


# ── Main QCM response ─────────────────────────────────────────────────────────

class QCMResponse(BaseModel):
    """QCM as returned to the student (correct answers hidden)."""
    id          : str
    session_id  : str
    title       : str
    topic       : str
    difficulty  : QCMDifficulty
    status      : QCMStatus
    num_questions: int
    questions   : list[QCMQuestionSchema]
    grade_report: Optional[QCMGradeReportSchema] = None
    created_at  : datetime
    submitted_at: Optional[datetime]
    evaluated_at: Optional[datetime]

    class Config:
        from_attributes = True


class QCMResultsResponse(QCMResponse):
    """QCM results — includes correct answers and explanations."""
    questions: list[QCMQuestionWithAnswerSchema]  # type: ignore[assignment]


class QCMListResponse(BaseModel):
    qcms : list[QCMResponse]
    total: int


# ── Requests ───────────────────────────────────────────────────────────────────

class QCMGenerateRequest(BaseModel):
    topic        : str          = Field(..., min_length=2, max_length=300)
    num_questions: int          = Field(default=5, ge=1, le=20)
    difficulty   : QCMDifficulty = QCMDifficulty.MEDIUM
    title        : Optional[str] = Field(default=None, max_length=200)


class QCMAnswerItem(BaseModel):
    question_order: int
    answer        : str   # "A" | "B" | "C" | "D"


class QCMSubmitRequest(BaseModel):
    answers: list[QCMAnswerItem]


# ── Workflow graph (for visualization) ────────────────────────────────────────

class WorkflowNodeSchema(BaseModel):
    id         : str
    label      : str
    type       : str             # "start" | "agent" | "end"
    agent_type : Optional[str]  = None   # "retrieval" | "generation" | "correction" | "evaluation"
    description: str
    inputs     : list[str]      = []
    outputs    : list[str]      = []


class WorkflowEdgeSchema(BaseModel):
    source: str
    target: str
    label : str
    type  : str = "direct"       # "direct" | "conditional"


class WorkflowGraphResponse(BaseModel):
    workflow_name: str
    description  : str
    nodes        : list[WorkflowNodeSchema]
    edges        : list[WorkflowEdgeSchema]
    state_schema : dict[str, str]
