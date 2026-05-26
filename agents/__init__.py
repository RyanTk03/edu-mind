"""
EDU-MIND AI Agents Package.

This package contains:
- norm.py: Core agent functions (generate_feedback, generate_exercise, correct_answer)
- rag.py: RAG system with ChromaDB
- router.py: Intent classification
- workflow.py: LangGraph multi-agent orchestration
"""

from .norm import (
    AgentState,
    generate_feedback,
    generate_exercise,
    correct_answer,
)

from .rag import (
    create_collection,
    delete_collection,
    ingest_text,
    ingest_pdf,
    ingest_documents,
    get_context,
    get_context_with_scores,
    get_collection_stats,
)

from .router import (
    classify_intent,
    get_intent,
    quick_intent,
    IntentClassification,
)

from .workflow import (
    workflow,
    chat,
    create_initial_state,
    build_workflow,
)

from .qcm_agents import (
    QCMState,
    generate_qcm,
    correct_qcm,
    correct_qcm_question,
    evaluate_grade,
)

from .orchestrator import (
    qcm_workflow,
    generate_qcm_workflow,
    submit_qcm_answers_workflow,
    get_workflow_graph_metadata,
    build_qcm_workflow,
)

__all__ = [
    # State
    "AgentState",
    # Core agents
    "generate_feedback",
    "generate_exercise",
    "correct_answer",
    # RAG
    "create_collection",
    "delete_collection",
    "ingest_text",
    "ingest_pdf",
    "ingest_documents",
    "get_context",
    "get_context_with_scores",
    "get_collection_stats",
    # Router
    "classify_intent",
    "get_intent",
    "quick_intent",
    "IntentClassification",
    # Workflow
    "workflow",
    "chat",
    "create_initial_state",
    "build_workflow",
    # QCM Agents
    "QCMState",
    "generate_qcm",
    "correct_qcm",
    "correct_qcm_question",
    "evaluate_grade",
    # QCM Orchestrator
    "qcm_workflow",
    "generate_qcm_workflow",
    "submit_qcm_answers_workflow",
    "get_workflow_graph_metadata",
    "build_qcm_workflow",
]
