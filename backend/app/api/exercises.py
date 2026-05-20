"""Exercise endpoints."""

from datetime import datetime, timezone

from beanie import PydanticObjectId
from fastapi import APIRouter

from app.core.deps import CurrentUser
from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.models.exercise import Exercise, ExerciseStatus
from app.models.session import Session
from app.schemas.exercise import (
    ExerciseGenerateRequest,
    ExerciseListResponse,
    ExerciseResponse,
    ExerciseResultsResponse,
    ExerciseSubmitRequest,
    QuestionOptionResponse,
    QuestionResponse,
    QuestionWithAnswerResponse,
)

router = APIRouter(prefix="/sessions/{session_id}/exercises", tags=["Exercises"])


async def verify_session_ownership(
    session_id: str, current_user: CurrentUser
) -> Session:
    """Verify session exists and belongs to current user."""
    try:
        session = await Session.get(PydanticObjectId(session_id))
    except Exception:
        raise NotFoundError("Session not found")

    if not session:
        raise NotFoundError("Session not found")

    if session.user.ref.id != current_user.id:
        raise ForbiddenError("Not your session")

    return session


def question_to_response(question) -> QuestionResponse:
    """Convert question to response (without correct answer)."""
    return QuestionResponse(
        order=question.order,
        type=question.type,
        question_text=question.question_text,
        options=[
            QuestionOptionResponse(label=o.label, text=o.text)
            for o in question.options
        ],
        user_answer=question.user_answer,
        is_correct=question.is_correct,
    )


def question_to_full_response(question) -> QuestionWithAnswerResponse:
    """Convert question to response with correct answer."""
    return QuestionWithAnswerResponse(
        order=question.order,
        type=question.type,
        question_text=question.question_text,
        options=[
            QuestionOptionResponse(label=o.label, text=o.text)
            for o in question.options
        ],
        user_answer=question.user_answer,
        is_correct=question.is_correct,
        correct_answer=question.correct_answer,
        gap_analysis=question.gap_analysis,
    )


def exercise_to_response(exercise: Exercise) -> ExerciseResponse:
    """Convert exercise model to response schema."""
    return ExerciseResponse(
        id=str(exercise.id),
        session_id=str(exercise.session.ref.id),
        title=exercise.title,
        mode=exercise.mode,
        status=exercise.status,
        questions=[question_to_response(q) for q in exercise.questions],
        total_score=exercise.total_score,
        created_at=exercise.created_at,
        completed_at=exercise.completed_at,
    )


def exercise_to_results_response(exercise: Exercise) -> ExerciseResultsResponse:
    """Convert exercise to results response with full details."""
    return ExerciseResultsResponse(
        id=str(exercise.id),
        session_id=str(exercise.session.ref.id),
        title=exercise.title,
        mode=exercise.mode,
        status=exercise.status,
        questions=[question_to_full_response(q) for q in exercise.questions],
        total_score=exercise.total_score,
        created_at=exercise.created_at,
        completed_at=exercise.completed_at,
    )


@router.get("/", response_model=ExerciseListResponse)
async def list_exercises(session_id: str, current_user: CurrentUser):
    """List all exercises for a session."""
    session = await verify_session_ownership(session_id, current_user)

    exercises = await Exercise.find(Exercise.session.id == session.id).to_list()

    return ExerciseListResponse(
        exercises=[exercise_to_response(e) for e in exercises],
        total=len(exercises),
    )


@router.post("/generate", response_model=ExerciseResponse)
async def generate_exercise(
    session_id: str, data: ExerciseGenerateRequest, current_user: CurrentUser
):
    """Generate a new exercise (placeholder - requires AI agent integration)."""
    session = await verify_session_ownership(session_id, current_user)

    # TODO: AI agent integration
    # For now, create an empty exercise that can be populated later
    # Later, the exercise agent will:
    # 1. Get user profile (level, weak_points)
    # 2. Query ChromaDB for relevant content
    # 3. Generate questions based on mode

    title = data.title or f"Exercise - {data.mode.value}"

    exercise = Exercise(
        session=session,
        title=title,
        mode=data.mode,
        status=ExerciseStatus.PENDING,
        questions=[],  # AI agent will populate this
    )
    await exercise.insert()

    return exercise_to_response(exercise)


@router.get("/{exercise_id}", response_model=ExerciseResponse)
async def get_exercise(
    session_id: str, exercise_id: str, current_user: CurrentUser
):
    """Get an exercise (without correct answers)."""
    session = await verify_session_ownership(session_id, current_user)

    try:
        exercise = await Exercise.get(PydanticObjectId(exercise_id))
    except Exception:
        raise NotFoundError("Exercise not found")

    if not exercise:
        raise NotFoundError("Exercise not found")

    if exercise.session.ref.id != session.id:
        raise ForbiddenError("Exercise doesn't belong to this session")

    return exercise_to_response(exercise)


@router.post("/{exercise_id}/submit", response_model=ExerciseResultsResponse)
async def submit_exercise(
    session_id: str,
    exercise_id: str,
    data: ExerciseSubmitRequest,
    current_user: CurrentUser,
):
    """Submit answers for an exercise."""
    session = await verify_session_ownership(session_id, current_user)

    try:
        exercise = await Exercise.get(PydanticObjectId(exercise_id))
    except Exception:
        raise NotFoundError("Exercise not found")

    if not exercise:
        raise NotFoundError("Exercise not found")

    if exercise.session.ref.id != session.id:
        raise ForbiddenError("Exercise doesn't belong to this session")

    if exercise.status == ExerciseStatus.COMPLETED:
        raise BadRequestError("Exercise already completed")

    # Process answers
    answer_map = {a.question_order: a.answer for a in data.answers}
    correct_count = 0

    for question in exercise.questions:
        if question.order in answer_map:
            question.user_answer = answer_map[question.order]
            question.answered_at = datetime.now(timezone.utc)

            # Simple correctness check (for QCM)
            # TODO: AI agent for open/code questions
            question.is_correct = (
                question.user_answer.strip().lower()
                == question.correct_answer.strip().lower()
            )

            if question.is_correct:
                correct_count += 1

    # Calculate score
    if exercise.questions:
        exercise.total_score = (correct_count / len(exercise.questions)) * 100

    exercise.status = ExerciseStatus.COMPLETED
    exercise.completed_at = datetime.now(timezone.utc)
    await exercise.save()

    # TODO: Update user profile with weak/strong points (AI agent)

    return exercise_to_results_response(exercise)


@router.get("/{exercise_id}/results", response_model=ExerciseResultsResponse)
async def get_exercise_results(
    session_id: str, exercise_id: str, current_user: CurrentUser
):
    """Get detailed exercise results (including correct answers)."""
    session = await verify_session_ownership(session_id, current_user)

    try:
        exercise = await Exercise.get(PydanticObjectId(exercise_id))
    except Exception:
        raise NotFoundError("Exercise not found")

    if not exercise:
        raise NotFoundError("Exercise not found")

    if exercise.session.ref.id != session.id:
        raise ForbiddenError("Exercise doesn't belong to this session")

    if exercise.status != ExerciseStatus.COMPLETED:
        raise BadRequestError("Exercise not yet completed")

    return exercise_to_results_response(exercise)
