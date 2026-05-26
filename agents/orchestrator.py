"""
QCM Orchestrator — LangGraph multi-agent workflow for EDU-MIND.

This module wires together:
  RAG retrieval → QCM generator → (student answers) → QCM corrector → Grade evaluator

It also exposes workflow graph metadata so the frontend can visualize
the pipeline via the /api/sessions/{id}/qcm/workflow-graph endpoint.
"""

from __future__ import annotations

from typing import Literal, Optional

from langgraph.graph import END, StateGraph

from .qcm_agents import (
    QCMState,
    correct_qcm,
    evaluate_grade,
    generate_qcm,
)
from .rag import get_context


# ══════════════════════════════════════════════════════════════════════════════
# NODE FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════


def qcm_rag_node(state: QCMState) -> dict:
    """
    [1] RAG Retrieval
    Fetch relevant document chunks from ChromaDB for the requested topic.
    """
    session_id = state.get("session_id", "default")
    topic      = state.get("topic", "")
    num_q      = state.get("num_questions", 5)

    # Retrieve more chunks for longer QCMs
    k = min(10 + num_q, 20)
    context = get_context(session_id=session_id, query=topic, k=k)

    return {"context": context}


def qcm_generator_node(state: QCMState) -> dict:
    """
    [2] QCM Generator Agent
    Generates num_questions MCQs grounded in the retrieved context.
    """
    questions = generate_qcm(
        topic         = state.get("topic", ""),
        num_questions = state.get("num_questions", 5),
        context       = state.get("context", []),
        difficulty    = state.get("difficulty", "medium"),
        student_level = state.get("student_level", 0.5),
    )
    return {"questions": questions}


def qcm_corrector_node(state: QCMState) -> dict:
    """
    [3] QCM Corrector Agent
    Corrects each student answer against the expected answer and RAG context.
    Only executed when student_answers is provided.
    """
    corrected = correct_qcm(
        questions      = state.get("questions", []),
        student_answers = state.get("student_answers", []),
        context        = state.get("context", []),
    )
    return {"corrected_questions": corrected}


def grade_evaluator_node(state: QCMState) -> dict:
    """
    [4] Grade Evaluator Agent
    Produces a structured grade report and updates the student level.
    """
    grade_report, updated_level = evaluate_grade(
        corrected_questions = state.get("corrected_questions", []),
        context             = state.get("context", []),
        student_level       = state.get("student_level", 0.5),
    )
    return {
        "grade_report"  : grade_report,
        "updated_level" : updated_level,
    }


# ══════════════════════════════════════════════════════════════════════════════
# ROUTING
# ══════════════════════════════════════════════════════════════════════════════


def _should_correct(state: QCMState) -> Literal["correct", "end"]:
    """
    After generation:
    - If student_answers is already provided  → go directly to correction.
    - Otherwise                               → stop (client will submit answers later).
    """
    answers = state.get("student_answers")
    if answers and len(answers) > 0:
        return "correct"
    return "end"


# ══════════════════════════════════════════════════════════════════════════════
# GRAPH BUILDER
# ══════════════════════════════════════════════════════════════════════════════


def build_qcm_workflow() -> StateGraph:
    """
    Build and compile the QCM multi-agent workflow.

    Graph structure:
        START
          │
        [rag]  ← retrieve context from ChromaDB
          │
        [qcm_generator]  ← generate N questions
          │
     ┌────┴────────────────────┐
  student_answers?         no answers yet
     │                         │
   [qcm_corrector]           END  ← client submits answers later
     │
   [grade_evaluator]
     │
    END
    """
    graph = StateGraph(QCMState)

    # Nodes
    graph.add_node("rag",            qcm_rag_node)
    graph.add_node("qcm_generator",  qcm_generator_node)
    graph.add_node("qcm_corrector",  qcm_corrector_node)
    graph.add_node("grade_evaluator",grade_evaluator_node)

    # Entry
    graph.set_entry_point("rag")

    # RAG → generator
    graph.add_edge("rag", "qcm_generator")

    # Generator → conditional (correct now vs stop)
    graph.add_conditional_edges(
        "qcm_generator",
        _should_correct,
        {"correct": "qcm_corrector", "end": END},
    )

    # Corrector → evaluator → end
    graph.add_edge("qcm_corrector",  "grade_evaluator")
    graph.add_edge("grade_evaluator", END)

    return graph.compile()


# Singleton compiled workflow
qcm_workflow = build_qcm_workflow()


# ══════════════════════════════════════════════════════════════════════════════
# WORKFLOW GRAPH METADATA  (for frontend visualization)
# ══════════════════════════════════════════════════════════════════════════════


def get_workflow_graph_metadata() -> dict:
    """
    Return a JSON-serialisable description of the workflow graph
    suitable for rendering in the frontend.

    The schema follows a simple node/edge/group format that the
    React visualizer component consumes directly.
    """
    nodes = [
        {
            "id"         : "START",
            "label"      : "START",
            "type"       : "start",
            "description": "Entry point — receives session_id, topic, num_questions",
        },
        {
            "id"         : "rag",
            "label"      : "RAG Retrieval",
            "type"       : "agent",
            "agent_type" : "retrieval",
            "description": "Queries ChromaDB to retrieve relevant document chunks for the topic.",
            "inputs"     : ["session_id", "topic"],
            "outputs"    : ["context (list[str])"],
        },
        {
            "id"         : "qcm_generator",
            "label"      : "QCM Generator",
            "type"       : "agent",
            "agent_type" : "generation",
            "description": "Generates N multiple-choice questions grounded in RAG context.",
            "inputs"     : ["topic", "num_questions", "difficulty", "student_level", "context"],
            "outputs"    : ["questions (list[QCMQuestion])"],
        },
        {
            "id"         : "qcm_corrector",
            "label"      : "QCM Corrector",
            "type"       : "agent",
            "agent_type" : "correction",
            "description": "Corrects each student answer using deterministic check + LLM gap analysis.",
            "inputs"     : ["questions", "student_answers", "context"],
            "outputs"    : ["corrected_questions (list[QCMCorrectedQuestion])"],
        },
        {
            "id"         : "grade_evaluator",
            "label"      : "Grade Evaluator",
            "type"       : "agent",
            "agent_type" : "evaluation",
            "description": "Produces a structured grade report and updates the student proficiency level.",
            "inputs"     : ["corrected_questions", "context", "student_level"],
            "outputs"    : ["grade_report", "updated_level"],
        },
        {
            "id"         : "END",
            "label"      : "END",
            "type"       : "end",
            "description": "Terminal node — returns final state to the API layer.",
        },
    ]

    edges = [
        {"source": "START",         "target": "rag",            "label": ""},
        {"source": "rag",           "target": "qcm_generator",  "label": "context retrieved"},
        {
            "source" : "qcm_generator",
            "target" : "qcm_corrector",
            "label"  : "student_answers provided",
            "type"   : "conditional",
        },
        {
            "source" : "qcm_generator",
            "target" : "END",
            "label"  : "no answers yet",
            "type"   : "conditional",
        },
        {"source": "qcm_corrector",   "target": "grade_evaluator", "label": ""},
        {"source": "grade_evaluator", "target": "END",             "label": ""},
    ]

    return {
        "workflow_name": "QCM Orchestrator",
        "description"  : (
            "Multi-agent pipeline: RAG retrieval → QCM generation → "
            "answer correction → grade evaluation."
        ),
        "nodes": nodes,
        "edges": edges,
        "state_schema": {
            "session_id"          : "str",
            "topic"               : "str",
            "num_questions"       : "int (1-20)",
            "difficulty"          : "easy | medium | hard",
            "student_level"       : "float (0.0-1.0)",
            "context"             : "list[str]",
            "questions"           : "list[QCMQuestion] | None",
            "student_answers"     : "list[str] | None",
            "corrected_questions" : "list[QCMCorrectedQuestion] | None",
            "grade_report"        : "QCMGradeReport | None",
            "updated_level"       : "float | None",
        },
    }


# ══════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ══════════════════════════════════════════════════════════════════════════════


def generate_qcm_workflow(
    session_id   : str,
    topic        : str,
    num_questions: int,
    difficulty   : str = "medium",
    student_level: float = 0.5,
) -> dict:
    """
    Run the generation phase only (RAG → generator).

    Returns:
        State dict with 'questions' key populated.
    """
    initial: QCMState = {
        "session_id"          : session_id,
        "topic"               : topic,
        "num_questions"       : num_questions,
        "difficulty"          : difficulty,
        "student_level"       : student_level,
        "context"             : [],
        "questions"           : None,
        "student_answers"     : None,   # no answers → workflow stops after generation
        "corrected_questions" : None,
        "grade_report"        : None,
        "updated_level"       : None,
    }
    return dict(qcm_workflow.invoke(initial))


def submit_qcm_answers_workflow(
    session_id      : str,
    topic           : str,
    questions       : list[dict],
    student_answers : list[str],
    context         : list[str],
    student_level   : float = 0.5,
) -> dict:
    """
    Run the correction + evaluation phase only.
    (questions and context are already known from generation.)

    Returns:
        State dict with 'corrected_questions', 'grade_report', 'updated_level'.
    """
    initial: QCMState = {
        "session_id"          : session_id,
        "topic"               : topic,
        "num_questions"       : len(questions),
        "difficulty"          : "medium",   # not relevant for correction
        "student_level"       : student_level,
        "context"             : context,
        "questions"           : questions,
        "student_answers"     : student_answers,
        "corrected_questions" : None,
        "grade_report"        : None,
        "updated_level"       : None,
    }

    # We only need corrector + evaluator, but invoking the full graph
    # with context already set means rag_node will just return existing context.
    # Use direct agent calls for clarity and performance:
    corrected     = correct_qcm(questions, student_answers, context)
    grade, level  = evaluate_grade(corrected, context, student_level)

    return {
        **initial,
        "corrected_questions": corrected,
        "grade_report"       : grade,
        "updated_level"      : level,
    }
