"""Exercise-related schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.exercise import ExerciseMode, ExerciseStatus, QuestionType


class QuestionOptionResponse(BaseModel):
    """Schema for question option."""

    label: str
    text: str


class QuestionResponse(BaseModel):
    """Schema for question response."""

    order: int
    type: QuestionType
    question_text: str
    options: list[QuestionOptionResponse]
    user_answer: Optional[str]
    is_correct: Optional[bool]

    class Config:
        from_attributes = True


class QuestionWithAnswerResponse(QuestionResponse):
    """Schema for question with correct answer (after submission)."""

    correct_answer: str
    gap_analysis: Optional[str]


class ExerciseGenerateRequest(BaseModel):
    """Schema for exercise generation request."""

    mode: ExerciseMode = ExerciseMode.FREE
    title: Optional[str] = Field(default=None, max_length=200)
    num_questions: int = Field(default=5, ge=1, le=20)


class AnswerSubmission(BaseModel):
    """Schema for a single answer submission."""

    question_order: int
    answer: str


class ExerciseSubmitRequest(BaseModel):
    """Schema for submitting exercise answers."""

    answers: list[AnswerSubmission]


class ExerciseResponse(BaseModel):
    """Schema for exercise response."""

    id: str
    session_id: str
    title: str
    mode: ExerciseMode
    status: ExerciseStatus
    questions: list[QuestionResponse]
    total_score: Optional[float]
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class ExerciseResultsResponse(BaseModel):
    """Schema for exercise results with full details."""

    id: str
    session_id: str
    title: str
    mode: ExerciseMode
    status: ExerciseStatus
    questions: list[QuestionWithAnswerResponse]
    total_score: Optional[float]
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class ExerciseListResponse(BaseModel):
    """Schema for list of exercises."""

    exercises: list[ExerciseResponse]
    total: int
