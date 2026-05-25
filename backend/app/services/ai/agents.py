"""
Core AI Agents for EDU-MIND.

Contains:
- FeedbackAgent: Generates pedagogical responses
- ExerciseAgent: Generates adaptive exercises
- CorrectionAgent: Grades answers with gap analysis
"""

import json
from typing import List, Optional

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt
from pydantic import BaseModel

from .config import ai_settings


def _get_llm() -> ChatGroq:
    """Get configured LLM instance."""
    return ChatGroq(
        model=ai_settings.model_name,
        api_key=ai_settings.groq_api_key,
        temperature=ai_settings.temperature,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# FEEDBACK AGENT
# ═══════════════════════════════════════════════════════════════════════════════

_FEEDBACK_PROMPT = ChatPromptTemplate.from_template(
    """Tu es un tuteur pédagogique expert et bienveillant.

DOCUMENTS DE RÉFÉRENCE :
{context}

QUESTION DE L'ÉLÈVE :
{question}

{correction_info}

INSTRUCTIONS :
- Réponds en te basant UNIQUEMENT sur les documents fournis
- Explique de manière claire et pédagogique
- Utilise des exemples si nécessaire
- Encourage l'élève
- Si tu ne trouves pas l'information dans les documents, dis-le honnêtement

RÉPONSE :"""
)


def generate_feedback(
    question: str,
    context: list[str],
    correction: Optional[dict] = None,
) -> str:
    """
    Generate a pedagogical response for a student question.

    Args:
        question: The student's question.
        context: List of relevant RAG chunks.
        correction: Optional correction result from CorrectionAgent.

    Returns:
        Pedagogical response string.
    """
    context_text = "\n\n".join(context) if context else "Aucun document fourni."

    correction_info = ""
    if correction:
        errors = ", ".join(correction.get("errors", [])) or "Aucune"
        hints = ", ".join(correction.get("feedback_hints", [])) or "Aucun"
        correction_info = (
            f"RÉSULTAT DE L'EXERCICE PRÉCÉDENT :\n"
            f"- Correct : {correction.get('is_correct', 'N/A')}\n"
            f"- Score   : {correction.get('score', 'N/A')}\n"
            f"- Erreurs : {errors}\n"
            f"- Pistes  : {hints}\n\n"
            f"Prends en compte ce résultat pour aider l'élève à comprendre ses erreurs."
        )

    chain = _FEEDBACK_PROMPT | _get_llm()

    response = chain.invoke({
        "question": question,
        "context": context_text,
        "correction_info": correction_info,
    })

    return response.content


# ═══════════════════════════════════════════════════════════════════════════════
# EXERCISE AGENT
# ═══════════════════════════════════════════════════════════════════════════════

_DIFFICULTY_MAP = {
    "easy": "Débutant — questions simples de mémorisation et compréhension",
    "medium": "Intermédiaire — questions d'application et d'analyse",
    "hard": "Avancé — questions de synthèse et résolution de problèmes complexes",
}

_EXERCISE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", (
        "Tu es un Agent Générateur d'Exercices expert et pédagogue.\n"
        "Génère des exercices en français, parfaitement adaptés aux consignes.\n\n"
        "CONTEXTE DU COURS :\n{context}\n\n"
        "PROFIL DE L'APPRENANT :\n{learner_profile}\n"
    )),
    ("human", (
        "Génère UN exercice sur le sujet : {topic}\n"
        "Niveau de difficulté : {difficulty_label}\n\n"
        "Réponds UNIQUEMENT en JSON valide, sans texte autour, sans balises markdown :\n"
        "{{\n"
        '  "question"        : "<énoncé complet de la question>",\n'
        '  "expected_answer" : "<réponse attendue détaillée>",\n'
        '  "hints"           : ["<indice 1>", "<indice 2>"]\n'
        "}}"
    )),
])


def generate_exercise(
    topic: str,
    difficulty: str = "medium",
    context: Optional[list[str]] = None,
    student_level: float = 0.5,
    history: Optional[list[dict]] = None,
) -> dict:
    """
    Generate an exercise adapted to the topic and student level.

    Args:
        topic: Exercise topic.
        difficulty: "easy" | "medium" | "hard".
        context: List of relevant RAG chunks.
        student_level: Student level between 0.0 and 1.0.
        history: Recent exercise history.

    Returns:
        Dict with question, expected_answer, and hints.
    """
    context_text = "\n\n".join(context) if context else (
        "Pas de support spécifique fourni. Utilise tes connaissances générales."
    )

    difficulty_label = _DIFFICULTY_MAP.get(difficulty, _DIFFICULTY_MAP["medium"])

    learner_profile = f"Niveau actuel : {student_level:.2f} / 1.00\n"
    if history:
        last = history[-3:]
        learner_profile += f"Derniers exercices : {last}"
    else:
        learner_profile += "Aucun historique disponible."

    chain = _EXERCISE_PROMPT | _get_llm() | StrOutputParser()

    raw = chain.invoke({
        "topic": topic,
        "difficulty_label": difficulty_label,
        "context": context_text,
        "learner_profile": learner_profile,
    })

    # Clean and parse JSON
    raw = raw.strip()
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1] if len(parts) > 1 else raw
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        exercise = json.loads(raw)
    except json.JSONDecodeError:
        exercise = {
            "question": raw,
            "expected_answer": "",
            "hints": [],
        }

    # Ensure required fields
    exercise.setdefault("question", "")
    exercise.setdefault("expected_answer", "")
    exercise.setdefault("hints", [])

    return exercise


# ═══════════════════════════════════════════════════════════════════════════════
# CORRECTION AGENT (with LangGraph workflow)
# ═══════════════════════════════════════════════════════════════════════════════

from typing import TypedDict


class _CorrectionState(TypedDict):
    """Internal state for correction workflow."""
    exercise: dict
    student_answer: str
    sources: List[str]
    student_level: float
    formatted_context: str
    llm_inferred_answer: str
    correction_result: dict
    identified_gaps: List[str]
    updated_level: float
    correction_reasoning: str
    needs_human_review: bool
    human_feedback: Optional[str]


_INFER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", (
        "Tu es un expert pédagogique.\n"
        "On te donne une question et des extraits de cours.\n"
        "Ton rôle : lire les sources et déterminer quelle est la bonne réponse.\n\n"
        "Réponds UNIQUEMENT avec la bonne réponse attendue, en une phrase courte."
    )),
    ("human", (
        "## Question\n{question}\n\n"
        "## Sources du cours\n{formatted_context}\n\n"
        "Quelle est la réponse correcte à cette question ?"
    )),
])

_GAP_ANALYSIS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", (
        "Tu es un analyste pédagogique expert.\n"
        "Un étudiant vient de répondre incorrectement à une question.\n"
        "Ton rôle : identifier POURQUOI il s'est trompé "
        "en te basant STRICTEMENT sur les sources du cours fournies.\n\n"
        "Réponds UNIQUEMENT en JSON valide, sans texte autour, sans balises markdown :\n"
        "{{\n"
        '  "likely_misconception" : "<idée fausse probable de l\'étudiant>",\n'
        '  "gaps"                 : ["<concept non maîtrisé 1>", "<concept 2>"],\n'
        '  "distractor_analysis"  : "<pourquoi cette réponse erronée semblait plausible>",\n'
        '  "feedback_hints"       : ["<conseil concret 1>", "<conseil 2>"]\n'
        "}}"
    )),
    ("human", (
        "## Question\n{question}\n\n"
        "## Réponse attendue\n{expected_answer}\n\n"
        "## Réponse de l'étudiant\n{student_answer}\n\n"
        "## Sources du cours\n{formatted_context}\n\n"
        "Analyse l'erreur de l'étudiant."
    )),
])


def _retrieve_node(state: _CorrectionState) -> _CorrectionState:
    """Format RAG sources into text context."""
    sources = state.get("sources", [])
    if not sources:
        state["formatted_context"] = "Aucune source disponible."
        return state

    state["formatted_context"] = "\n\n".join(
        f"[Source {i+1}]\n{chunk}" for i, chunk in enumerate(sources)
    )
    return state


def _infer_answer_node(state: _CorrectionState) -> _CorrectionState:
    """Ask LLM to confirm/infer correct answer from sources."""
    llm = _get_llm()
    chain = _INFER_PROMPT | llm
    response = chain.invoke({
        "question": state["exercise"].get("question", ""),
        "formatted_context": state["formatted_context"],
    })
    state["llm_inferred_answer"] = response.content.strip()
    return state


def _mcq_check_node(state: _CorrectionState) -> _CorrectionState:
    """Deterministic correction: compare student answer to expected."""
    student = state["student_answer"].strip()
    expected = state["exercise"].get("expected_answer", "")
    inferred = state.get("llm_inferred_answer", expected)

    # For MCQ (single letter), direct comparison
    is_single_letter = len(student) == 1 and student.upper() in "ABCD"
    if is_single_letter:
        correct_letter = expected.strip().upper()[:1] if len(expected.strip()) == 1 else ""
        is_correct = student.upper() == correct_letter if correct_letter else False
        valid_choice = True
    else:
        # Open answer: delegate to gap_analysis
        is_correct = False
        valid_choice = bool(student)

    state["correction_result"] = {
        "score": 1.0 if is_correct else 0.0,
        "verdict": "correct" if is_correct else "incorrect",
        "is_correct": is_correct,
        "student_answer": student,
        "expected_answer": expected,
        "valid_choice": valid_choice,
        "ambiguous": False,
    }
    return state


def _ambiguity_check(state: _CorrectionState) -> str:
    """Router: empty/invalid response → HITL, else → gap_analysis."""
    if not state["correction_result"].get("valid_choice", True):
        state["needs_human_review"] = True
        return "hitl"
    state["needs_human_review"] = False
    return "gap_analysis"


def _hitl_node(state: _CorrectionState) -> _CorrectionState:
    """Suspend execution for human review on invalid response."""
    human_input = interrupt({
        "message": "Réponse invalide — révision humaine requise",
        "question": state["exercise"].get("question", ""),
        "student_answer": state["student_answer"],
    })

    if human_input:
        state["human_feedback"] = human_input.get("comment", "")
        if "score" in human_input:
            score = float(human_input["score"])
            state["correction_result"]["score"] = score
            state["correction_result"]["is_correct"] = score >= 0.5
            state["correction_result"]["verdict"] = "correct" if score >= 0.5 else "incorrect"
        if "gaps" in human_input:
            state["identified_gaps"] = human_input["gaps"]

    return state


def _gap_analysis_node(state: _CorrectionState) -> _CorrectionState:
    """LLM analysis of learning gaps (only if incorrect)."""
    result = state["correction_result"]

    if result["is_correct"]:
        state["identified_gaps"] = []
        state["correction_reasoning"] = "Réponse correcte."
        return state

    llm = _get_llm()
    chain = _GAP_ANALYSIS_PROMPT | llm
    response = chain.invoke({
        "question": state["exercise"].get("question", ""),
        "expected_answer": state["exercise"].get("expected_answer", ""),
        "student_answer": state["student_answer"],
        "formatted_context": state["formatted_context"],
    })

    raw = response.content.strip()
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1] if len(parts) > 1 else raw
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        analysis = json.loads(raw)
    except json.JSONDecodeError:
        analysis = {
            "likely_misconception": "Analyse non disponible.",
            "gaps": [],
            "distractor_analysis": "",
            "feedback_hints": [],
        }

    state["identified_gaps"] = analysis.get("gaps", [])
    state["correction_reasoning"] = json.dumps(analysis, ensure_ascii=False)
    state["correction_result"]["feedback_hints"] = analysis.get("feedback_hints", [])
    state["correction_result"]["errors"] = analysis.get("gaps", [])

    return state


def _update_level_node(state: _CorrectionState) -> _CorrectionState:
    """Recalculate student level (asymmetric moving average)."""
    score = state["correction_result"]["score"]
    previous_level = state.get("student_level", 0.5)

    alpha = ai_settings.alpha_correct if score == 1.0 else ai_settings.alpha_incorrect
    new_level = alpha * score + (1 - alpha) * previous_level
    new_level = round(max(ai_settings.level_min, min(ai_settings.level_max, new_level)), 3)

    state["updated_level"] = new_level
    return state


def _build_correction_graph():
    """Build and compile the correction workflow."""
    graph = StateGraph(_CorrectionState)

    graph.add_node("retrieve", _retrieve_node)
    graph.add_node("infer_answer", _infer_answer_node)
    graph.add_node("mcq_check", _mcq_check_node)
    graph.add_node("hitl", _hitl_node)
    graph.add_node("gap_analysis", _gap_analysis_node)
    graph.add_node("update_level", _update_level_node)

    graph.set_entry_point("retrieve")
    graph.add_edge("retrieve", "infer_answer")
    graph.add_edge("infer_answer", "mcq_check")

    graph.add_conditional_edges(
        "mcq_check",
        _ambiguity_check,
        {"hitl": "hitl", "gap_analysis": "gap_analysis"},
    )

    graph.add_edge("hitl", "gap_analysis")
    graph.add_edge("gap_analysis", "update_level")
    graph.add_edge("update_level", END)

    return graph.compile(
        checkpointer=MemorySaver(),
        interrupt_before=["hitl"],
    )


_correction_graph = _build_correction_graph()


def correct_answer(
    exercise: dict,
    student_answer: str,
    context: Optional[list[str]] = None,
    student_level: float = 0.5,
    session_id: str = "default",
) -> dict:
    """
    Correct a student's answer and return structured result.

    Args:
        exercise: Dict with question and expected_answer.
        student_answer: Student's free response.
        context: Relevant RAG chunks.
        student_level: Current student level (0.0-1.0).
        session_id: Session ID for checkpointer.

    Returns:
        Dict with is_correct, score, errors, feedback_hints, updated_level, verdict.
    """
    initial_state: _CorrectionState = {
        "exercise": exercise,
        "student_answer": student_answer,
        "sources": context or [],
        "student_level": student_level,
        "formatted_context": "",
        "llm_inferred_answer": "",
        "correction_result": {},
        "identified_gaps": [],
        "updated_level": student_level,
        "correction_reasoning": "",
        "needs_human_review": False,
        "human_feedback": None,
    }

    config = {"configurable": {"thread_id": session_id}}
    result = _correction_graph.invoke(initial_state, config=config)

    correction = result.get("correction_result", {})
    return {
        "is_correct": correction.get("is_correct", False),
        "score": correction.get("score", 0.0),
        "errors": result.get("identified_gaps", []),
        "feedback_hints": correction.get("feedback_hints", []),
        "updated_level": result.get("updated_level", student_level),
        "verdict": correction.get("verdict", "incorrect"),
    }
