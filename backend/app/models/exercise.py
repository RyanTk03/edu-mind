from datetime import datetime
from enum import Enum
from typing import Optional

from beanie import Document, Link
from pydantic import BaseModel, Field

from app.models.session import Session


class QuestionType(str, Enum):
    """Type of question."""

    QCM = "qcm"
    OPEN = "open"
    CODE = "code"


class ExerciseMode(str, Enum):
    """Exercise generation mode."""

    EVALUATION = "evaluation"  # Diagnostic test
    REINFORCEMENT = "reinforcement"  # Practice weak points
    FREE = "free"  # General practice


class ExerciseStatus(str, Enum):
    """Exercise completion status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class QuestionOption(BaseModel):
    """Option for QCM question."""

    label: str  # A, B, C, D
    text: str


class Question(BaseModel):
    """Embedded question within an exercise."""

    order: int
    type: QuestionType
    question_text: str
    options: list[QuestionOption] = Field(default_factory=list)  # For QCM
    correct_answer: str
    user_answer: Optional[str] = None
    is_correct: Optional[bool] = None
    gap_analysis: Optional[str] = None  # From correction agent
    answered_at: Optional[datetime] = None


class Exercise(Document):
    """Exercise document containing multiple questions."""

    session: Link[Session]
    title: str
    mode: ExerciseMode
    status: ExerciseStatus = ExerciseStatus.PENDING
    questions: list[Question] = Field(default_factory=list)
    total_score: Optional[float] = None  # Percentage 0-100
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    class Settings:
        name = "exercises"
