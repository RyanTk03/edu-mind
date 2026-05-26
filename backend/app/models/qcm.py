"""QCM document model for MongoDB via Beanie."""

from datetime import datetime
from enum import Enum
from typing import Optional

from beanie import Document, Link
from pydantic import BaseModel, Field

from app.models.session import Session


class QCMDifficulty(str, Enum):
    EASY   = "easy"
    MEDIUM = "medium"
    HARD   = "hard"


class QCMStatus(str, Enum):
    GENERATED  = "generated"   # questions created, awaiting student answers
    SUBMITTED  = "submitted"   # student submitted answers
    EVALUATED  = "evaluated"   # grade report produced


class QCMOption(BaseModel):
    """Single option (A/B/C/D) within a QCM question."""
    label: str   # "A" | "B" | "C" | "D"
    text : str


class QCMQuestion(BaseModel):
    """Embedded question within a QCM document."""
    order          : int
    question_text  : str
    options        : list[QCMOption] = Field(default_factory=list)
    correct_answer : str                          # "A" | "B" | "C" | "D"
    explanation    : str = ""                     # Source-grounded explanation
    # Filled after submission
    student_answer : Optional[str]   = None
    is_correct     : Optional[bool]  = None
    score          : Optional[float] = None       # 0.0 or 1.0
    feedback       : Optional[str]   = None
    gap_analysis   : Optional[str]   = None


class QCMGradeReport(BaseModel):
    """Embedded grade report produced by GradeEvaluatorAgent."""
    total_score    : float          # 0.0 → 100.0
    correct_count  : int
    total_questions: int
    grade_letter   : str            # A / B / C / D / F
    grade_label    : str            # Excellent / Bien / ...
    strong_points  : list[str] = Field(default_factory=list)
    weak_points    : list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    summary        : str = ""


class QCM(Document):
    """QCM document — one per generation request."""

    session     : Link[Session]
    title       : str
    topic       : str
    difficulty  : QCMDifficulty = QCMDifficulty.MEDIUM
    status      : QCMStatus     = QCMStatus.GENERATED
    num_questions: int

    questions   : list[QCMQuestion] = Field(default_factory=list)
    grade_report: Optional[QCMGradeReport] = None

    # Student level snapshot at generation time
    student_level_at_generation: float = 0.5
    # Updated level after evaluation
    updated_student_level: Optional[float] = None

    created_at  : datetime = Field(default_factory=datetime.utcnow)
    submitted_at: Optional[datetime] = None
    evaluated_at: Optional[datetime] = None

    class Settings:
        name = "qcms"
