"""
QCM endpoints.

Routes:
  POST   /sessions/{session_id}/qcm/generate          → generate questions
  GET    /sessions/{session_id}/qcm/                  → list all QCMs
  GET    /sessions/{session_id}/qcm/{qcm_id}          → get one QCM (no answers)
  POST   /sessions/{session_id}/qcm/{qcm_id}/submit   → submit answers → grade
  GET    /sessions/{session_id}/qcm/{qcm_id}/results  → full results with answers
  GET    /sessions/{session_id}/qcm/workflow-graph     → LangGraph visualization data
"""

from datetime import datetime, timezone

from beanie import PydanticObjectId
from fastapi import APIRouter

from app.api import check_link_id, get_link_id
from app.core.deps import CurrentUser
from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.models.qcm import (
    QCM,
    QCMDifficulty,
    QCMGradeReport,
    QCMOption,
    QCMQuestion,
    QCMStatus,
)
from app.models.session import Session
from app.models.user import UserProfile
from app.schemas.qcm import (
    QCMAnswerItem,
    QCMGenerateRequest,
    QCMGradeReportSchema,
    QCMListResponse,
    QCMOptionSchema,
    QCMQuestionSchema,
    QCMQuestionWithAnswerSchema,
    QCMResponse,
    QCMResultsResponse,
    QCMSubmitRequest,
    WorkflowEdgeSchema,
    WorkflowGraphResponse,
    WorkflowNodeSchema,
)
from app.services.qcm_service import QCMService

router = APIRouter(prefix="/sessions/{session_id}/qcm", tags=["QCM"])


# ── Helpers ────────────────────────────────────────────────────────────────────


async def _verify_session(session_id: str, current_user: CurrentUser) -> Session:
    try:
        session = await Session.get(PydanticObjectId(session_id))
    except Exception:
        raise NotFoundError("Session not found")
    if not session:
        raise NotFoundError("Session not found")
    if not check_link_id(session.user, current_user.id):
        raise ForbiddenError("Not your session")
    return session


async def _verify_qcm(qcm_id: str, session: Session) -> QCM:
    try:
        qcm = await QCM.get(PydanticObjectId(qcm_id))
    except Exception:
        raise NotFoundError("QCM not found")
    if not qcm:
        raise NotFoundError("QCM not found")
    if not check_link_id(qcm.session, session.id):
        raise ForbiddenError("QCM doesn't belong to this session")
    return qcm


def _question_to_schema(q: QCMQuestion) -> QCMQuestionSchema:
    return QCMQuestionSchema(
        order         = q.order,
        question_text = q.question_text,
        options       = [QCMOptionSchema(label=o.label, text=o.text) for o in q.options],
        student_answer= q.student_answer,
        is_correct    = q.is_correct,
        score         = q.score,
        feedback      = q.feedback,
        gap_analysis  = q.gap_analysis,
    )


def _question_to_full_schema(q: QCMQuestion) -> QCMQuestionWithAnswerSchema:
    return QCMQuestionWithAnswerSchema(
        order         = q.order,
        question_text = q.question_text,
        options       = [QCMOptionSchema(label=o.label, text=o.text) for o in q.options],
        correct_answer= q.correct_answer,
        explanation   = q.explanation,
        student_answer= q.student_answer,
        is_correct    = q.is_correct,
        score         = q.score,
        feedback      = q.feedback,
        gap_analysis  = q.gap_analysis,
    )


def _grade_to_schema(gr: QCMGradeReport) -> QCMGradeReportSchema:
    return QCMGradeReportSchema(
        total_score     = gr.total_score,
        correct_count   = gr.correct_count,
        total_questions = gr.total_questions,
        grade_letter    = gr.grade_letter,
        grade_label     = gr.grade_label,
        strong_points   = gr.strong_points,
        weak_points     = gr.weak_points,
        recommendations = gr.recommendations,
        summary         = gr.summary,
    )


def _qcm_to_response(qcm: QCM) -> QCMResponse:
    return QCMResponse(
        id            = str(qcm.id),
        session_id    = get_link_id(qcm.session),
        title         = qcm.title,
        topic         = qcm.topic,
        difficulty    = qcm.difficulty,
        status        = qcm.status,
        num_questions = qcm.num_questions,
        questions     = [_question_to_schema(q) for q in qcm.questions],
        grade_report  = _grade_to_schema(qcm.grade_report) if qcm.grade_report else None,
        created_at    = qcm.created_at,
        submitted_at  = qcm.submitted_at,
        evaluated_at  = qcm.evaluated_at,
    )


def _qcm_to_results_response(qcm: QCM) -> QCMResultsResponse:
    return QCMResultsResponse(
        id            = str(qcm.id),
        session_id    = get_link_id(qcm.session),
        title         = qcm.title,
        topic         = qcm.topic,
        difficulty    = qcm.difficulty,
        status        = qcm.status,
        num_questions = qcm.num_questions,
        questions     = [_question_to_full_schema(q) for q in qcm.questions],
        grade_report  = _grade_to_schema(qcm.grade_report) if qcm.grade_report else None,
        created_at    = qcm.created_at,
        submitted_at  = qcm.submitted_at,
        evaluated_at  = qcm.evaluated_at,
    )


# ── Endpoints ──────────────────────────────────────────────────────────────────


@router.get("/workflow-graph", response_model=WorkflowGraphResponse)
async def get_workflow_graph(session_id: str, current_user: CurrentUser):
    """
    Return the LangGraph workflow graph metadata for frontend visualization.
    No AI call — pure metadata.
    """
    await _verify_session(session_id, current_user)
    data = await QCMService.get_workflow_graph()

    return WorkflowGraphResponse(
        workflow_name = data["workflow_name"],
        description   = data["description"],
        nodes = [WorkflowNodeSchema(**n) for n in data["nodes"]],
        edges = [WorkflowEdgeSchema(**e) for e in data["edges"]],
        state_schema  = data["state_schema"],
    )


@router.get("/", response_model=QCMListResponse)
async def list_qcms(session_id: str, current_user: CurrentUser):
    """List all QCMs for a session."""
    session = await _verify_session(session_id, current_user)
    qcms = await QCM.find(QCM.session.id == session.id).to_list()
    return QCMListResponse(
        qcms  = [_qcm_to_response(q) for q in qcms],
        total = len(qcms),
    )


@router.post("/generate", response_model=QCMResponse)
async def generate_qcm(
    session_id: str,
    data      : QCMGenerateRequest,
    current_user: CurrentUser,
):
    """
    Generate a new QCM using the QCMGeneratorAgent.

    The number of questions is specified by the client.
    Questions are grounded in the session's uploaded documents (RAG).
    """
    session = await _verify_session(session_id, current_user)

    # Get student level from profile
    profile = await UserProfile.find_one(UserProfile.user.id == current_user.id)
    student_level = profile.level_score if profile else 0.5

    # Determine difficulty string
    difficulty_str = data.difficulty.value

    # Run AI generation (thread pool)
    ai_questions = await QCMService.generate(
        session_id    = session_id,
        topic         = data.topic,
        num_questions = data.num_questions,
        difficulty    = difficulty_str,
        student_level = student_level,
    )

    # Map AI output → model objects
    questions: list[QCMQuestion] = []
    for q in ai_questions:
        options = [
            QCMOption(label=o["label"], text=o["text"])
            for o in q.get("options", [])
        ]
        questions.append(QCMQuestion(
            order          = q.get("order", len(questions) + 1),
            question_text  = q.get("question_text", ""),
            options        = options,
            correct_answer = q.get("correct_answer", "A"),
            explanation    = q.get("explanation", ""),
        ))

    title = data.title or f"QCM — {data.topic}"

    qcm = QCM(
        session      = session,
        title        = title,
        topic        = data.topic,
        difficulty   = data.difficulty,
        status       = QCMStatus.GENERATED,
        num_questions= data.num_questions,
        questions    = questions,
        student_level_at_generation = student_level,
    )
    await qcm.insert()

    return _qcm_to_response(qcm)


@router.get("/{qcm_id}", response_model=QCMResponse)
async def get_qcm(session_id: str, qcm_id: str, current_user: CurrentUser):
    """Get a QCM without revealing correct answers."""
    session = await _verify_session(session_id, current_user)
    qcm     = await _verify_qcm(qcm_id, session)
    return _qcm_to_response(qcm)


@router.post("/{qcm_id}/submit", response_model=QCMResultsResponse)
async def submit_qcm(
    session_id  : str,
    qcm_id      : str,
    data        : QCMSubmitRequest,
    current_user: CurrentUser,
):
    """
    Submit student answers for a QCM.

    Triggers:
    1. QCMCorrectorAgent — corrects each question
    2. GradeEvaluatorAgent — produces full grade report + updated student level
    """
    session = await _verify_session(session_id, current_user)
    qcm     = await _verify_qcm(qcm_id, session)

    if qcm.status == QCMStatus.EVALUATED:
        raise BadRequestError("QCM already evaluated")

    # Get current student level
    profile = await UserProfile.find_one(UserProfile.user.id == current_user.id)
    student_level = profile.level_score if profile else 0.5

    # Build answer list ordered by question.order
    answer_map = {a.question_order: a.answer for a in data.answers}
    student_answers = [
        answer_map.get(q.order, "")
        for q in sorted(qcm.questions, key=lambda q: q.order)
    ]

    # Build question dicts for the AI (no correct_answer exposed externally)
    questions_dicts = [
        {
            "order"          : q.order,
            "question_text"  : q.question_text,
            "options"        : [{"label": o.label, "text": o.text} for o in q.options],
            "correct_answer" : q.correct_answer,
            "explanation"    : q.explanation,
        }
        for q in qcm.questions
    ]

    # Run correction + evaluation
    result = await QCMService.submit(
        session_id      = session_id,
        topic           = qcm.topic,
        questions       = questions_dicts,
        student_answers = student_answers,
        student_level   = student_level,
    )

    corrected     = result["corrected_questions"]
    grade_data    = result["grade_report"]
    updated_level = result.get("updated_level", student_level)

    # Update question objects
    corrected_map = {c["order"]: c for c in corrected}
    for q in qcm.questions:
        c = corrected_map.get(q.order, {})
        q.student_answer = c.get("student_answer")
        q.is_correct     = c.get("is_correct")
        q.score          = c.get("score")
        q.feedback       = c.get("feedback", "")
        q.gap_analysis   = c.get("gap_analysis", "")

    # Build grade report model
    qcm.grade_report = QCMGradeReport(
        total_score     = grade_data.get("total_score",     0.0),
        correct_count   = grade_data.get("correct_count",   0),
        total_questions = grade_data.get("total_questions", len(qcm.questions)),
        grade_letter    = grade_data.get("grade_letter",    "F"),
        grade_label     = grade_data.get("grade_label",     "Insuffisant"),
        strong_points   = grade_data.get("strong_points",   []),
        weak_points     = grade_data.get("weak_points",     []),
        recommendations = grade_data.get("recommendations", []),
        summary         = grade_data.get("summary",         ""),
    )

    qcm.status       = QCMStatus.EVALUATED
    qcm.submitted_at = datetime.now(timezone.utc)
    qcm.evaluated_at = datetime.now(timezone.utc)
    qcm.updated_student_level = updated_level
    await qcm.save()

    # Update user profile
    if profile:
        profile.level_score = updated_level
        for wp in grade_data.get("weak_points", []):
            if wp and wp not in profile.weak_points:
                profile.weak_points.append(wp)
        profile.weak_points = profile.weak_points[-20:]
        await profile.save()

    return _qcm_to_results_response(qcm)


@router.get("/{qcm_id}/results", response_model=QCMResultsResponse)
async def get_qcm_results(session_id: str, qcm_id: str, current_user: CurrentUser):
    """Get full QCM results including correct answers and grade report."""
    session = await _verify_session(session_id, current_user)
    qcm     = await _verify_qcm(qcm_id, session)

    if qcm.status != QCMStatus.EVALUATED:
        raise BadRequestError("QCM not yet evaluated — submit answers first")

    return _qcm_to_results_response(qcm)
