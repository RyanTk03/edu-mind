"""
Intent Router for EDU-MIND.

Classifies user intent into: question, exercise, or answer.
"""

from typing import Literal

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from .config import ai_settings


# ═══════════════════════════════════════════════════════════════════════════════
# SCHEMA
# ═══════════════════════════════════════════════════════════════════════════════


class IntentClassification(BaseModel):
    """Classification result for user intent."""

    intent: Literal["question", "exercise", "answer"] = Field(
        description=(
            "The user's intent: "
            "'question' for asking/learning/explanations, "
            "'exercise' for requesting practice/quiz/exercises, "
            "'answer' for submitting a response to an ongoing exercise"
        )
    )
    confidence: float = Field(
        description="Confidence score between 0.0 and 1.0",
        ge=0.0,
        le=1.0,
    )
    reasoning: str = Field(
        description="Brief explanation of why this intent was chosen"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# PROMPT
# ═══════════════════════════════════════════════════════════════════════════════

_ROUTER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """Tu es un classificateur d'intentions pour une application éducative française.

Ton rôle est de déterminer ce que l'utilisateur veut faire.

CONTEXTE DE LA SESSION:
- Exercice en cours: {has_exercise}
- L'exercice attend une réponse: {awaiting_answer}

RÈGLES DE CLASSIFICATION:
1. "question" → L'élève pose une question, demande une explication, veut comprendre un concept
   - Exemples: "Explique-moi les dérivées", "C'est quoi une fonction?", "Je ne comprends pas"

2. "exercise" → L'élève demande un exercice, un quiz, de la pratique
   - Exemples: "Donne-moi un exercice", "Je veux m'entraîner", "Un quiz sur les matrices"

3. "answer" → L'élève soumet une réponse à un exercice EN COURS
   - IMPORTANT: Ne classifier comme "answer" QUE si un exercice est en cours ET attend une réponse
   - Exemples: "La réponse est 42", "C", "x = 5", une formule mathématique

ATTENTION:
- Si pas d'exercice en cours et l'élève donne juste un mot/chiffre, c'est probablement une "question"
- En cas de doute, préfère "question"

{format_instructions}"""),
    ("human", 'Message de l\'élève: "{user_message}"'),
])

_parser = PydanticOutputParser(pydantic_object=IntentClassification)


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════════


def _get_router_llm() -> ChatGroq:
    """Get the router LLM instance (fast, cheap model)."""
    return ChatGroq(
        model=ai_settings.router_model,
        api_key=ai_settings.groq_api_key,
        temperature=0,  # Deterministic
    )


def classify_intent(
    user_message: str,
    has_exercise: bool = False,
    awaiting_answer: bool = False,
) -> IntentClassification:
    """
    Classify user intent using LLM.

    Args:
        user_message: The user's message to classify.
        has_exercise: Whether there's an ongoing exercise.
        awaiting_answer: Whether the exercise is waiting for an answer.

    Returns:
        IntentClassification with intent, confidence, and reasoning.
    """
    llm = _get_router_llm()
    chain = _ROUTER_PROMPT | llm | _parser

    result = chain.invoke({
        "user_message": user_message,
        "has_exercise": "Oui" if has_exercise else "Non",
        "awaiting_answer": "Oui" if awaiting_answer else "Non",
        "format_instructions": _parser.get_format_instructions(),
    })

    return result


def get_intent(
    user_message: str,
    has_exercise: bool = False,
    awaiting_answer: bool = False,
) -> str:
    """
    Get just the intent string (simplified interface).

    Args:
        user_message: The user's message to classify.
        has_exercise: Whether there's an ongoing exercise.
        awaiting_answer: Whether the exercise is waiting for an answer.

    Returns:
        Intent string: "question", "exercise", or "answer".
    """
    result = classify_intent(user_message, has_exercise, awaiting_answer)
    return result.intent


# ═══════════════════════════════════════════════════════════════════════════════
# FALLBACK (Rule-based)
# ═══════════════════════════════════════════════════════════════════════════════

_EXERCISE_KEYWORDS = {
    "exercice", "exercices", "quiz", "qcm", "test", "pratique",
    "entraîne", "entrainer", "entraîner", "évalue",
    "évaluation", "contrôle", "devoir",
}

_QUESTION_KEYWORDS = {
    "explique", "expliquer", "comment", "pourquoi", "quoi", "quel",
    "quelle", "qu'est", "c'est", "aide", "comprends", "comprendre",
    "définition", "signifie", "différence",
}


def quick_intent(
    user_message: str,
    has_exercise: bool = False,
    awaiting_answer: bool = False,
) -> str:
    """
    Quick rule-based intent detection (fallback if LLM unavailable).

    Args:
        user_message: The user's message to classify.
        has_exercise: Whether there's an ongoing exercise.
        awaiting_answer: Whether the exercise is waiting for an answer.

    Returns:
        Intent string: "question", "exercise", or "answer".
    """
    message_lower = user_message.lower().strip()
    words = set(message_lower.split())

    # If awaiting answer and short message, likely an answer
    if awaiting_answer and len(message_lower) < 200:
        if words & _QUESTION_KEYWORDS:
            return "question"
        return "answer"

    # Check for exercise keywords
    if words & _EXERCISE_KEYWORDS:
        return "exercise"

    # Default to question
    return "question"
