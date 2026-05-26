"""
QCM (Multiple-Choice Questions) Agents for EDU-MIND.

Contains three specialized agents:
  - QCMGeneratorAgent : generates a full QCM from RAG sources
  - QCMCorrectorAgent : corrects each answer using RAG context
  - GradeEvaluatorAgent : produces a structured grade report

All agents are RAG-grounded: they ONLY use content retrieved from
the user's uploaded documents via ChromaDB.
"""

from __future__ import annotations

import json
import os
from typing import Optional, TypedDict

from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langgraph.graph import END, StateGraph

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────
_MODEL      = "llama-3.3-70b-versatile"
_FAST_MODEL = "llama-3.1-8b-instant"
_TEMP       = 0.6


def _llm(fast: bool = False) -> ChatGroq:
    return ChatGroq(
        model=_FAST_MODEL if fast else _MODEL,
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=_TEMP,
    )


# ══════════════════════════════════════════════════════════════════════════════
# SHARED STATE
# ══════════════════════════════════════════════════════════════════════════════

class QCMState(TypedDict):
    """
    Shared state flowing through the QCM orchestrator graph.

    Generation phase:
        session_id, num_questions, topic, difficulty, context
        → questions (list of QCMQuestion dicts)

    Correction phase:
        questions + student_answers (list of str)
        → corrected_questions (list of QCMCorrectedQuestion dicts)

    Evaluation phase:
        corrected_questions + student_level
        → grade_report (QCMGradeReport dict)
        → updated_level (float)
    """

    # ── Session ───────────────────────────────────────────────────────────────
    session_id      : str
    topic           : str
    num_questions   : int                # 1 → 20
    difficulty      : str                # "easy" | "medium" | "hard"
    student_level   : float              # 0.0 → 1.0

    # ── RAG ───────────────────────────────────────────────────────────────────
    context         : list[str]          # Chunks from ChromaDB

    # ── Generation output ─────────────────────────────────────────────────────
    questions       : list[dict] | None
    # Each dict:
    # {
    #   "order"          : int,
    #   "question_text"  : str,
    #   "options"        : [{"label": "A", "text": "..."}, ...],
    #   "correct_answer" : "A" | "B" | "C" | "D",
    #   "explanation"    : str   ← why this answer is correct (from sources)
    # }

    # ── Correction phase ──────────────────────────────────────────────────────
    student_answers : list[str] | None   # e.g. ["A", "C", "B", ...]

    corrected_questions : list[dict] | None
    # Each dict extends the question dict with:
    # {
    #   "student_answer" : str,
    #   "is_correct"     : bool,
    #   "score"          : float,   # 0.0 or 1.0
    #   "feedback"       : str,     # pedagogical feedback
    #   "gap_analysis"   : str,     # why wrong (if incorrect)
    # }

    # ── Grade report ──────────────────────────────────────────────────────────
    grade_report    : dict | None
    # {
    #   "total_score"    : float,   # 0 → 100
    #   "correct_count"  : int,
    #   "total_questions": int,
    #   "grade_letter"   : str,     # A / B / C / D / F
    #   "grade_label"    : str,     # "Excellent" / ...
    #   "strong_points"  : list[str],
    #   "weak_points"    : list[str],
    #   "recommendations": list[str],
    #   "summary"        : str,
    # }

    updated_level   : float | None


# ══════════════════════════════════════════════════════════════════════════════
# 1. QCM GENERATOR AGENT
# ══════════════════════════════════════════════════════════════════════════════

_DIFFICULTY_LABELS = {
    "easy"  : "Débutant — mémorisation et compréhension simple",
    "medium": "Intermédiaire — application et analyse",
    "hard"  : "Avancé — synthèse, nuances et résolution de problèmes",
}

_GEN_SYSTEM = (
    "Tu es un expert en création de QCM pédagogiques.\n"
    "Tu génères des questions à choix multiples EXCLUSIVEMENT à partir "
    "des documents de cours fournis.\n\n"
    "RÈGLES ABSOLUES :\n"
    "- Chaque question doit avoir exactement 4 options (A, B, C, D)\n"
    "- Une seule bonne réponse par question\n"
    "- La bonne réponse doit être vérifiable dans les documents fournis\n"
    "- Les distracteurs (mauvaises réponses) doivent être plausibles\n"
    "- Langue : français\n\n"
    "CONTEXTE DES DOCUMENTS :\n{context}\n\n"
    "PROFIL DE L'APPRENANT : niveau {student_level:.2f}/1.00 — difficulté demandée : {difficulty_label}"
)

_GEN_HUMAN = (
    "Génère exactement {num_questions} question(s) QCM sur le sujet : \"{topic}\".\n\n"
    "Réponds UNIQUEMENT en JSON valide, sans texte ni balises markdown :\n"
    "[\n"
    "  {{\n"
    '    "order"         : 1,\n'
    '    "question_text" : "<énoncé de la question>",\n'
    '    "options"       : [\n'
    '      {{"label": "A", "text": "<option A>"}},\n'
    '      {{"label": "B", "text": "<option B>"}},\n'
    '      {{"label": "C", "text": "<option C>"}},\n'
    '      {{"label": "D", "text": "<option D>"}}\n'
    "    ],\n"
    '    "correct_answer": "A",\n'
    '    "explanation"   : "<explication basée sur les sources>"\n'
    "  }},\n"
    "  ...\n"
    "]"
)

_GEN_PROMPT = ChatPromptTemplate.from_messages([
    ("system", _GEN_SYSTEM),
    ("human",  _GEN_HUMAN),
])


def generate_qcm(
    topic         : str,
    num_questions : int,
    context       : list[str],
    difficulty    : str = "medium",
    student_level : float = 0.5,
) -> list[dict]:
    """
    Generate a QCM grounded in the RAG context.

    Args:
        topic         : Subject for the QCM.
        num_questions : How many questions to generate (1-20).
        context       : RAG chunks retrieved from ChromaDB.
        difficulty    : "easy" | "medium" | "hard".
        student_level : Current student level 0.0 → 1.0.

    Returns:
        List of question dicts with fields:
        order, question_text, options, correct_answer, explanation.
    """
    context_text    = "\n\n".join(context) if context else "Aucun document fourni."
    difficulty_label = _DIFFICULTY_LABELS.get(difficulty, _DIFFICULTY_LABELS["medium"])
    num_questions    = max(1, min(20, num_questions))

    chain = _GEN_PROMPT | _llm() | StrOutputParser()
    raw = chain.invoke({
        "context"        : context_text,
        "student_level"  : student_level,
        "difficulty_label": difficulty_label,
        "num_questions"  : num_questions,
        "topic"          : topic,
    })

    raw = _strip_json_fence(raw)

    try:
        questions = json.loads(raw)
    except json.JSONDecodeError:
        # Fallback: single empty question rather than crash
        questions = []

    # Normalise and validate each question
    validated: list[dict] = []
    for i, q in enumerate(questions):
        q.setdefault("order",          i + 1)
        q.setdefault("question_text",  "")
        q.setdefault("options",        [])
        q.setdefault("correct_answer", "A")
        q.setdefault("explanation",    "")
        validated.append(q)

    return validated


# ══════════════════════════════════════════════════════════════════════════════
# 2. QCM CORRECTOR AGENT
# ══════════════════════════════════════════════════════════════════════════════

_CORR_SYSTEM = (
    "Tu es un correcteur pédagogique expert.\n"
    "Ton rôle est de corriger les réponses d'un étudiant à un QCM "
    "en te basant UNIQUEMENT sur les documents de cours fournis.\n\n"
    "CONTEXTE DES DOCUMENTS :\n{context}"
)

_CORR_HUMAN = (
    "Question n°{order} : {question_text}\n\n"
    "Options :\n{options_text}\n\n"
    "Bonne réponse attendue : {correct_answer}\n"
    "Réponse de l'étudiant  : {student_answer}\n\n"
    "Réponds UNIQUEMENT en JSON valide :\n"
    "{{\n"
    '  "is_correct"  : true/false,\n'
    '  "score"       : 0.0 ou 1.0,\n'
    '  "feedback"    : "<retour pédagogique positif et encourageant>",\n'
    "  \"gap_analysis\": \"<uniquement si incorrect : pourquoi l'erreur et concept a revoir>\"\n"
    "}}"
)

_CORR_PROMPT = ChatPromptTemplate.from_messages([
    ("system", _CORR_SYSTEM),
    ("human",  _CORR_HUMAN),
])


def correct_qcm_question(
    question      : dict,
    student_answer: str,
    context       : list[str],
) -> dict:
    """
    Correct a single QCM question using RAG context.

    Args:
        question      : Question dict from generate_qcm().
        student_answer: The letter chosen by the student (A/B/C/D).
        context       : RAG chunks for grounding.

    Returns:
        Extended question dict with is_correct, score, feedback, gap_analysis.
    """
    context_text = "\n\n".join(context) if context else "Aucune source disponible."

    options_text = "\n".join(
        f"  {o['label']}. {o['text']}"
        for o in question.get("options", [])
    )

    # Deterministic check for single-letter answers
    correct = question.get("correct_answer", "").strip().upper()[:1]
    given   = (student_answer or "").strip().upper()[:1]
    is_correct_deterministic = (given == correct) if correct and given else False

    chain = _CORR_PROMPT | _llm(fast=True) | StrOutputParser()
    raw = chain.invoke({
        "context"        : context_text,
        "order"          : question.get("order", "?"),
        "question_text"  : question.get("question_text", ""),
        "options_text"   : options_text,
        "correct_answer" : correct or "?",
        "student_answer" : given or "(aucune réponse)",
    })

    raw = _strip_json_fence(raw)

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        result = {}

    # Merge deterministic check with LLM feedback
    result["is_correct"]   = is_correct_deterministic
    result["score"]         = 1.0 if is_correct_deterministic else 0.0
    result.setdefault("feedback",     "")
    result.setdefault("gap_analysis", "")

    corrected = {**question}
    corrected["student_answer"] = given
    corrected["is_correct"]     = result["is_correct"]
    corrected["score"]           = result["score"]
    corrected["feedback"]        = result["feedback"]
    corrected["gap_analysis"]    = result["gap_analysis"] if not result["is_correct"] else ""

    return corrected


def correct_qcm(
    questions     : list[dict],
    student_answers: list[str],
    context       : list[str],
) -> list[dict]:
    """
    Correct all questions in a QCM.

    Args:
        questions      : List of question dicts from generate_qcm().
        student_answers: List of answers ordered by question.order (e.g. ["A","B"]).
        context        : RAG chunks.

    Returns:
        List of corrected question dicts.
    """
    # Build answer map by order
    answer_map = {}
    for i, q in enumerate(questions):
        answer_map[q.get("order", i + 1)] = (
            student_answers[i] if i < len(student_answers) else ""
        )

    corrected: list[dict] = []
    for q in questions:
        ans = answer_map.get(q.get("order", 0), "")
        corrected.append(correct_qcm_question(q, ans, context))

    return corrected


# ══════════════════════════════════════════════════════════════════════════════
# 3. GRADE EVALUATOR AGENT
# ══════════════════════════════════════════════════════════════════════════════

_EVAL_SYSTEM = (
    "Tu es un évaluateur pédagogique expert.\n"
    "Tu analyses les résultats d'un QCM et produis un rapport de compétences "
    "détaillé, bienveillant et constructif.\n"
    "Base ton analyse sur les erreurs identifiées et les sources du cours.\n\n"
    "CONTEXTE DES DOCUMENTS :\n{context}"
)

_EVAL_HUMAN = (
    "Score obtenu : {correct_count}/{total_questions} ({pct:.1f}%)\n\n"
    "Détail par question :\n{summary_text}\n\n"
    "Réponds UNIQUEMENT en JSON valide :\n"
    "{{\n"
    '  "grade_letter"   : "A|B|C|D|F",\n'
    '  "grade_label"    : "Excellent|Bien|Assez bien|Passable|Insuffisant",\n'
    '  "strong_points"  : ["<compétence maîtrisée>", ...],\n'
    '  "weak_points"    : ["<concept à retravailler>", ...],\n'
    '  "recommendations": ["<conseil concret>", ...],\n'
    '  "summary"        : "<paragraphe de synthèse encourageant>"\n'
    "}}"
)

_EVAL_PROMPT = ChatPromptTemplate.from_messages([
    ("system", _EVAL_SYSTEM),
    ("human",  _EVAL_HUMAN),
])

_ALPHA_CORRECT   = 0.25
_ALPHA_INCORRECT = 0.10
_LEVEL_MIN       = 0.05
_LEVEL_MAX       = 0.95

_GRADE_THRESHOLDS = [
    (90, "A", "Excellent"),
    (75, "B", "Bien"),
    (60, "C", "Assez bien"),
    (50, "D", "Passable"),
    (0,  "F", "Insuffisant"),
]


def evaluate_grade(
    corrected_questions: list[dict],
    context            : list[str],
    student_level      : float = 0.5,
) -> tuple[dict, float]:
    """
    Produce a full grade report and update the student level.

    Args:
        corrected_questions: Output of correct_qcm().
        context            : RAG chunks.
        student_level      : Current student level 0.0 → 1.0.

    Returns:
        (grade_report dict, updated_level float)
    """
    total        = len(corrected_questions)
    correct_count = sum(1 for q in corrected_questions if q.get("is_correct"))
    pct          = (correct_count / total * 100) if total else 0.0

    # Determine grade letter deterministically
    grade_letter, grade_label = "F", "Insuffisant"
    for threshold, letter, label in _GRADE_THRESHOLDS:
        if pct >= threshold:
            grade_letter, grade_label = letter, label
            break

    # Build per-question summary for LLM
    lines = []
    for q in corrected_questions:
        status = "✅" if q.get("is_correct") else "❌"
        lines.append(
            f"{status} Q{q.get('order', '?')}: {q.get('question_text', '')[:80]}…\n"
            f"   Réponse étudiant: {q.get('student_answer', '?')} | "
            f"Correcte: {q.get('correct_answer', '?')}\n"
            f"   Gap: {q.get('gap_analysis', 'N/A')}"
        )
    summary_text = "\n\n".join(lines)

    context_text = "\n\n".join(context) if context else "Aucune source disponible."

    chain = _EVAL_PROMPT | _llm() | StrOutputParser()
    raw = chain.invoke({
        "context"       : context_text,
        "correct_count" : correct_count,
        "total_questions": total,
        "pct"           : pct,
        "summary_text"  : summary_text,
    })

    raw = _strip_json_fence(raw)

    try:
        llm_report = json.loads(raw)
    except json.JSONDecodeError:
        llm_report = {}

    grade_report = {
        "total_score"    : round(pct, 1),
        "correct_count"  : correct_count,
        "total_questions": total,
        "grade_letter"   : llm_report.get("grade_letter",    grade_letter),
        "grade_label"    : llm_report.get("grade_label",     grade_label),
        "strong_points"  : llm_report.get("strong_points",   []),
        "weak_points"    : llm_report.get("weak_points",     []),
        "recommendations": llm_report.get("recommendations", []),
        "summary"        : llm_report.get("summary",         ""),
    }

    # Update student level with asymmetric moving average
    norm_score   = pct / 100.0
    alpha        = _ALPHA_CORRECT if norm_score >= 0.5 else _ALPHA_INCORRECT
    updated_level = alpha * norm_score + (1 - alpha) * student_level
    updated_level = round(max(_LEVEL_MIN, min(_LEVEL_MAX, updated_level)), 3)

    return grade_report, updated_level


# ══════════════════════════════════════════════════════════════════════════════
# HELPER
# ══════════════════════════════════════════════════════════════════════════════

def _strip_json_fence(raw: str) -> str:
    """Remove ```json ... ``` fences from LLM output."""
    raw = raw.strip()
    if raw.startswith("```"):
        parts = raw.split("```")
        raw   = parts[1] if len(parts) > 1 else raw
        if raw.startswith("json"):
            raw = raw[4:]
    return raw.strip()
