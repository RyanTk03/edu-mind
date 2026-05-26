"""
QCM Workflow — backend/app/services/ai integration layer.

Thin wrappers around agents/qcm_agents.py and agents/orchestrator.py
that live under the backend service tree and are imported by qcm_service.py.
"""

from __future__ import annotations

from typing import Optional

# Import from the top-level agents package (monorepo layout)
# The agents/ folder is at repo root; the backend is run from repo root too.
try:
    from agents.qcm_agents import (
        QCMState,
        generate_qcm,
        correct_qcm,
        evaluate_grade,
    )
    from agents.orchestrator import (
        generate_qcm_workflow,
        submit_qcm_answers_workflow,
        get_workflow_graph_metadata,
    )
    from agents.rag import get_context
except ImportError:
    # Fallback: installed as package or different path layout
    from app.services.ai.qcm_agents_local import (  # type: ignore
        generate_qcm,
        correct_qcm,
        evaluate_grade,
        generate_qcm_workflow,
        submit_qcm_answers_workflow,
        get_workflow_graph_metadata,
        get_context,
    )


def run_generate_qcm(
    session_id   : str,
    topic        : str,
    num_questions: int,
    difficulty   : str  = "medium",
    student_level: float = 0.5,
    context      : Optional[list[str]] = None,
) -> list[dict]:
    """
    Generate QCM questions via the orchestrator workflow.

    Args:
        session_id: Session ID for RAG retrieval.
        topic: Topic for the QCM.
        num_questions: Number of questions to generate.
        difficulty: Difficulty level (easy, medium, hard).
        student_level: Student's current level (0.0-1.0).
        context: Pre-fetched context from RAG and conversation.

    Returns:
        List of question dicts with order, question_text, options,
        correct_answer, explanation.
    """
    # If no context provided, fetch from RAG
    if context is None:
        context = get_context(session_id=session_id, query=topic, k=10)

    result = generate_qcm_workflow(
        session_id    = session_id,
        topic         = topic,
        num_questions = num_questions,
        difficulty    = difficulty,
        student_level = student_level,
        context       = context,
    )
    return result.get("questions", [])


def run_submit_qcm(
    session_id      : str,
    topic           : str,
    questions       : list[dict],
    student_answers : list[str],
    student_level   : float = 0.5,
) -> dict:
    """
    Correct a QCM and produce a grade report.

    Returns:
        Dict with corrected_questions, grade_report, updated_level.
    """
    # Retrieve context fresh (same topic used during generation)
    context = get_context(session_id=session_id, query=topic, k=15)

    result = submit_qcm_answers_workflow(
        session_id      = session_id,
        topic           = topic,
        questions       = questions,
        student_answers = student_answers,
        context         = context,
        student_level   = student_level,
    )
    return {
        "corrected_questions": result.get("corrected_questions", []),
        "grade_report"       : result.get("grade_report", {}),
        "updated_level"      : result.get("updated_level", student_level),
    }


def get_qcm_workflow_graph() -> dict:
    """Return the workflow graph metadata for frontend visualization."""
    return get_workflow_graph_metadata()
