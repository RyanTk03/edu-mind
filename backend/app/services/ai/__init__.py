"""
AI Services Module for EDU-MIND.

This module contains all AI-related functionality:
- agents.py: Core agent functions (feedback, exercise, correction)
- rag.py: RAG system with ChromaDB
- router.py: Intent classification
- workflow.py: LangGraph multi-agent orchestration
"""

from .agents import generate_feedback, generate_exercise, correct_answer
from .rag import (
    create_collection,
    delete_collection,
    ingest_text,
    ingest_pdf,
    get_context,
    get_collection_stats,
)
from .router import classify_intent, get_intent
from .workflow import chat, AgentState
from .config import ai_settings

__all__ = [
    # Agents
    "generate_feedback",
    "generate_exercise",
    "correct_answer",
    # RAG
    "create_collection",
    "delete_collection",
    "ingest_text",
    "ingest_pdf",
    "get_context",
    "get_collection_stats",
    # Router
    "classify_intent",
    "get_intent",
    # Workflow
    "chat",
    "AgentState",
    # Config
    "ai_settings",
]
