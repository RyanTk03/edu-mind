"""
AI Service Layer for EDU-MIND Backend.

Provides a clean async interface between FastAPI routes and AI agents.
"""

from typing import Optional

from .ai import (
    chat,
    generate_exercise as _generate_exercise,
    correct_answer as _correct_answer,
    get_context,
    ingest_text,
    ingest_pdf,
    create_collection,
    get_collection_stats,
)


class AIService:
    """
    Service class for AI operations.

    All methods are async-compatible for FastAPI integration.
    """

    @staticmethod
    async def process_message(
        session_id: str,
        message: str,
        student_level: float = 0.5,
        history: Optional[list[dict]] = None,
        current_exercise: Optional[dict] = None,
    ) -> dict:
        """
        Process a user message through the AI workflow.

        Args:
            session_id: The session ID.
            message: User's message.
            student_level: Current student level (0.0-1.0).
            history: Previous exercise history.
            current_exercise: Ongoing exercise (if any).

        Returns:
            Dict with response, intent, current_exercise, correction, updated_level.
        """
        result = chat(
            session_id=session_id,
            message=message,
            student_level=student_level,
            history=history,
            current_exercise=current_exercise,
        )

        return {
            "response": result.get("response", ""),
            "intent": result.get("intent"),
            "current_exercise": result.get("current_exercise"),
            "correction": result.get("correction"),
            "updated_level": result.get("updated_level"),
            "context": result.get("context", []),
        }

    @staticmethod
    async def generate_exercise(
        session_id: str,
        topic: str,
        difficulty: str = "medium",
        student_level: float = 0.5,
        history: Optional[list[dict]] = None,
    ) -> dict:
        """
        Generate an exercise directly.

        Args:
            session_id: The session ID.
            topic: Exercise topic.
            difficulty: "easy", "medium", or "hard".
            student_level: Current student level (0.0-1.0).
            history: Previous exercise history.

        Returns:
            Exercise dict with question, expected_answer, hints.
        """
        context = get_context(session_id=session_id, query=topic, k=5)

        return _generate_exercise(
            topic=topic,
            difficulty=difficulty,
            context=context,
            student_level=student_level,
            history=history,
        )

    @staticmethod
    async def correct_answer(
        session_id: str,
        exercise: dict,
        student_answer: str,
        student_level: float = 0.5,
    ) -> dict:
        """
        Correct a student's answer.

        Args:
            session_id: The session ID.
            exercise: Exercise dict with question and expected_answer.
            student_answer: Student's submitted answer.
            student_level: Current student level (0.0-1.0).

        Returns:
            Correction result with is_correct, score, errors, etc.
        """
        context = get_context(
            session_id=session_id,
            query=exercise.get("question", ""),
            k=5,
        )

        return _correct_answer(
            exercise=exercise,
            student_answer=student_answer,
            context=context,
            student_level=student_level,
            session_id=session_id,
        )

    @staticmethod
    async def ingest_document(
        session_id: str,
        content: str,
        source: str = "document",
        metadata: Optional[dict] = None,
    ) -> int:
        """
        Ingest a document into the session's RAG collection.

        Args:
            session_id: The session ID.
            content: Document text content.
            source: Source identifier.
            metadata: Additional metadata.

        Returns:
            Number of chunks created.
        """
        return ingest_text(
            session_id=session_id,
            text=content,
            source=source,
            metadata=metadata,
        )

    @staticmethod
    async def ingest_pdf_file(
        session_id: str,
        pdf_path: str,
        metadata: Optional[dict] = None,
    ) -> int:
        """
        Ingest a PDF file into the session's RAG collection.

        Args:
            session_id: The session ID.
            pdf_path: Path to the PDF file.
            metadata: Additional metadata.

        Returns:
            Number of chunks created.
        """
        return ingest_pdf(
            session_id=session_id,
            pdf_path=pdf_path,
            metadata=metadata,
        )

    @staticmethod
    async def get_collection_info(session_id: str) -> dict:
        """Get information about a session's document collection."""
        return get_collection_stats(session_id)

    @staticmethod
    async def initialize_session(session_id: str) -> None:
        """Initialize a session's RAG collection."""
        create_collection(session_id)
