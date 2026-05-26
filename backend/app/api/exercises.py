"""Exercise endpoints."""

from datetime import datetime, timezone

from beanie import PydanticObjectId
from fastapi import APIRouter

from app.api import get_link_id, check_link_id
from app.core.deps import CurrentUser
from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.models.exercise import Exercise, ExerciseMode, ExerciseStatus, Question, QuestionType
from app.models.session import Session
from app.models.user import UserProfile
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
from app.services.ai_service import AIService

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

    if not check_link_id(session.user, current_user.id):
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
        session_id=get_link_id(exercise.session),
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
        session_id=get_link_id(exercise.session),
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
    """Generate a new exercise using AI."""
    session = await verify_session_ownership(session_id, current_user)

    # Get user profile for student level and weak points
    profile = await UserProfile.find_one(UserProfile.user.id == current_user.id)
    # Use 0.3 (beginner) for new users who haven't been assessed yet
    student_level = profile.level_score if (profile and profile.level_score is not None) else 0.3
    weak_points = profile.weak_points if profile else []

    # Determine topic based on mode
    if data.mode == ExerciseMode.REINFORCEMENT and weak_points:
        topic = f"Renforcement sur: {', '.join(weak_points[:3])}"
    else:
        topic = data.title or "Exercice général"

    # Determine difficulty based on student level
    if student_level < 0.35:
        difficulty = "easy"
    elif student_level < 0.65:
        difficulty = "medium"
    else:
        difficulty = "hard"

    # Get exercise history from session
    session_metadata = session.metadata or {}
    history = session_metadata.get("exercise_history", [])

    # Generate questions using AI
    questions = []
    for i in range(data.num_questions):
        # Generate one exercise at a time
        ai_exercise = await AIService.generate_exercise(
            session_id=session_id,
            topic=topic,
            difficulty=difficulty,
            student_level=student_level,
            history=history,
        )

        question = Question(
            order=i + 1,
            type=QuestionType.OPEN,  # AI generates open questions by default
            question_text=ai_exercise.get("question", ""),
            correct_answer=ai_exercise.get("expected_answer", ""),
            options=[],  # Could be extended for QCM
        )
        questions.append(question)

    title = data.title or f"Exercice - {data.mode.value}"

    exercise = Exercise(
        session=session,
        title=title,
        mode=data.mode,
        status=ExerciseStatus.IN_PROGRESS,
        questions=questions,
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

    if not check_link_id(exercise.session, session.id):
        raise ForbiddenError("Exercise doesn't belong to this session")

    return exercise_to_response(exercise)


@router.post("/{exercise_id}/submit", response_model=ExerciseResultsResponse)
async def submit_exercise(
    session_id: str,
    exercise_id: str,
    data: ExerciseSubmitRequest,
    current_user: CurrentUser,
):
    """Submit answers for an exercise with AI-powered correction."""
    session = await verify_session_ownership(session_id, current_user)

    try:
        exercise = await Exercise.get(PydanticObjectId(exercise_id))
    except Exception:
        raise NotFoundError("Exercise not found")

    if not exercise:
        raise NotFoundError("Exercise not found")

    if not check_link_id(exercise.session, session.id):
        raise ForbiddenError("Exercise doesn't belong to this session")

    if exercise.status == ExerciseStatus.COMPLETED:
        raise BadRequestError("Exercise already completed")

    # Get user profile for student level
    profile = await UserProfile.find_one(UserProfile.user.id == current_user.id)
    # Use 0.3 (beginner) for new users who haven't been assessed yet
    student_level = profile.level_score if (profile and profile.level_score is not None) else 0.3

    # Process answers
    answer_map = {a.question_order: a.answer for a in data.answers}
    correct_count = 0
    total_score_sum = 0.0
    all_errors = []

    for question in exercise.questions:
        if question.order in answer_map:
            question.user_answer = answer_map[question.order]
            question.answered_at = datetime.now(timezone.utc)

            # Use AI for correction
            correction = await AIService.correct_answer(
                session_id=session_id,
                exercise={
                    "question": question.question_text,
                    "expected_answer": question.correct_answer,
                },
                student_answer=question.user_answer,
                student_level=student_level,
            )

            question.is_correct = correction.get("is_correct", False)
            question.gap_analysis = ", ".join(correction.get("errors", []))
            total_score_sum += correction.get("score", 0.0)

            if question.is_correct:
                correct_count += 1

            # Collect errors for profile update
            all_errors.extend(correction.get("errors", []))

            # Update student level progressively
            if correction.get("updated_level"):
                student_level = correction["updated_level"]

    # Calculate final score
    if exercise.questions:
        exercise.total_score = (total_score_sum / len(exercise.questions)) * 100

    exercise.status = ExerciseStatus.COMPLETED
    exercise.completed_at = datetime.now(timezone.utc)
    await exercise.save()

    # Update session progress
    session.exercises_completed = (session.exercises_completed or 0) + 1
    exercise_score = (exercise.total_score or 0) / 100  # Convert to 0-1 scale
    if session.progress_score is None:
        session.progress_score = exercise_score
    else:
        # Rolling average
        n = session.exercises_completed
        session.progress_score = ((session.progress_score * (n - 1)) + exercise_score) / n
    await session.save()

    # Update user profile with weak points and new level
    if profile:
        # Set level_score (first assessment or update)
        if profile.level_score is None:
            profile.level_score = student_level
        else:
            profile.level_score = student_level
        profile.exercises_completed = (profile.exercises_completed or 0) + 1
        for error in all_errors:
            if error and error not in profile.weak_points:
                profile.weak_points.append(error)
        # Keep only last 20 weak points
        profile.weak_points = profile.weak_points[-20:]
        await profile.save()

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

    if not check_link_id(exercise.session, session.id):
        raise ForbiddenError("Exercise doesn't belong to this session")

    if exercise.status != ExerciseStatus.COMPLETED:
        raise BadRequestError("Exercise not yet completed")

    return exercise_to_results_response(exercise)
