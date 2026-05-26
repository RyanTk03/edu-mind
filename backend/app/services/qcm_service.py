"""
QCM Service — async bridge between FastAPI endpoints and the AI agents.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Optional

from app.services.ai.qcm_workflow import (
    get_qcm_workflow_graph,
    run_generate_qcm,
    run_submit_qcm,
)


class QCMService:
    """Async service for all QCM operations."""

    # ── Generation ─────────────────────────────────────────────────────────────

    @staticmethod
    async def generate(
        session_id   : str,
        topic        : str,
        num_questions: int,
        difficulty   : str  = "medium",
        student_level: float = 0.5,
    ) -> list[dict]:
        """
        Generate QCM questions in a thread pool (the agents are sync).

        Returns:
            List of question dicts ready to be stored in MongoDB.
        """
        loop = asyncio.get_event_loop()
        questions = await loop.run_in_executor(
            None,
            lambda: run_generate_qcm(
                session_id    = session_id,
                topic         = topic,
                num_questions = num_questions,
                difficulty    = difficulty,
                student_level = student_level,
            ),
        )
        return questions

    # ── Submission & correction ─────────────────────────────────────────────────

    @staticmethod
    async def submit(
        session_id     : str,
        topic          : str,
        questions      : list[dict],
        student_answers: list[str],
        student_level  : float = 0.5,
    ) -> dict:
        """
        Correct answers and evaluate grade in a thread pool.

        Returns:
            Dict with corrected_questions, grade_report, updated_level.
        """
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: run_submit_qcm(
                session_id      = session_id,
                topic           = topic,
                questions       = questions,
                student_answers = student_answers,
                student_level   = student_level,
            ),
        )
        return result

    # ── Workflow graph ──────────────────────────────────────────────────────────

    @staticmethod
    async def get_workflow_graph() -> dict:
        """Return LangGraph workflow metadata for the frontend visualizer."""
        return get_qcm_workflow_graph()
