"""
Multi-Agent Orchestration Workflow for EDU-MIND.

Uses LangGraph to coordinate RAG, Router, and all three agents.
"""

from typing import Literal, Optional, TypedDict

from langgraph.graph import StateGraph, END

from .agents import generate_feedback, generate_exercise, correct_answer
from .rag import get_context
from .router import classify_intent, quick_intent, classify_exercise_type, quick_exercise_type


# ═══════════════════════════════════════════════════════════════════════════════
# STATE DEFINITION
# ═══════════════════════════════════════════════════════════════════════════════


class AgentState(TypedDict):
    """
    Shared state between all agents in the workflow.

    Lifecycle:
        user_message → [RAG] → context → [Router] → intent
            → [ExerciseProposal] : exercise_proposal (user confirms)
            → [ExerciseAgent] : current_exercise
            → [CorrectionAgent] : correction
            → [FeedbackAgent] : response
    """

    # Session
    session_id: str
    collection_name: str

    # User input
    user_message: str

    # Student profile
    student_level: float  # 0.0 → 1.0
    history: list[dict]  # Recent exercise history
    conversation_history: list[dict]  # Recent chat messages for context

    # RAG output
    context: list[str]

    # Exercise proposal flow (AI suggests, user confirms)
    exercise_proposal: Optional[dict]  # {type, topic, num_questions, difficulty}
    exercise_type: Optional[Literal["qcm", "code", "open"]]

    # Exercise flow
    current_exercise: Optional[dict]
    student_answer: Optional[str]

    # Agent outputs
    correction: Optional[dict]
    response: Optional[str]

    # Routing - added "confirmation" for when user confirms/modifies proposal
    intent: Optional[Literal["question", "exercise", "answer", "confirmation"]]

    # Updated level (from CorrectionAgent)
    updated_level: Optional[float]


# ═══════════════════════════════════════════════════════════════════════════════
# NODE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════


def rag_node(state: AgentState) -> dict:
    """Retrieve relevant context from ChromaDB."""
    session_id = state.get("session_id", "default")
    user_message = state.get("user_message", "")

    # If there's a pending exercise proposal, use the topic for better RAG retrieval
    exercise_proposal = state.get("exercise_proposal")
    if exercise_proposal and exercise_proposal.get("topic"):
        query = exercise_proposal["topic"]
    else:
        query = user_message

    context = get_context(
        session_id=session_id,
        query=query,
        k=8,  # Increased for better context
    )

    return {"context": context}


def router_node(state: AgentState) -> dict:
    """Classify user intent using LLM router."""
    # If intent was pre-set (from frontend action), respect it
    pre_set_intent = state.get("intent")
    if pre_set_intent in ("confirmation", "answer"):
        return {}  # Don't override

    user_message = state.get("user_message", "")
    current_exercise = state.get("current_exercise")
    correction = state.get("correction")
    exercise_proposal = state.get("exercise_proposal")

    has_exercise = current_exercise is not None
    awaiting_answer = has_exercise and correction is None

    # Check if this is a confirmation of a pending proposal
    if exercise_proposal:
        message_lower = user_message.lower().strip()
        confirm_keywords = {"oui", "yes", "ok", "d'accord", "confirmer", "génère", "genere", "générer", "go"}
        reject_keywords = {"non", "no", "changer", "modifier", "autre"}

        if any(kw in message_lower for kw in confirm_keywords):
            return {"intent": "confirmation"}
        elif any(kw in message_lower for kw in reject_keywords):
            # Clear proposal and let user specify again
            return {"intent": "exercise", "exercise_proposal": None}

    try:
        result = classify_intent(
            user_message=user_message,
            has_exercise=has_exercise,
            awaiting_answer=awaiting_answer,
        )
        intent = result.intent
    except Exception:
        # Fallback to rule-based
        intent = quick_intent(
            user_message=user_message,
            has_exercise=has_exercise,
            awaiting_answer=awaiting_answer,
        )

    updates = {"intent": intent}

    if intent == "answer":
        updates["student_answer"] = user_message
    elif intent == "exercise":
        # Also classify exercise type
        try:
            type_result = classify_exercise_type(user_message)
            updates["exercise_type"] = type_result.exercise_type
            # Create proposal
            student_level = state.get("student_level", 0.5)
            difficulty = "easy" if student_level < 0.35 else "medium" if student_level < 0.65 else "hard"
            updates["exercise_proposal"] = {
                "type": type_result.exercise_type,
                "topic": type_result.topic,
                "num_questions": 5 if type_result.exercise_type == "qcm" else 1,
                "difficulty": difficulty,
            }
        except Exception:
            # Fallback
            ex_type, topic = quick_exercise_type(user_message)
            updates["exercise_type"] = ex_type
            student_level = state.get("student_level", 0.5)
            difficulty = "easy" if student_level < 0.35 else "medium" if student_level < 0.65 else "hard"
            updates["exercise_proposal"] = {
                "type": ex_type,
                "topic": topic,
                "num_questions": 5 if ex_type == "qcm" else 1,
                "difficulty": difficulty,
            }

    return updates


def route_by_intent(state: AgentState) -> str:
    """Route to appropriate agent based on intent."""
    intent = state.get("intent", "question")

    if intent == "exercise":
        return "exercise_proposal"  # Show proposal first
    elif intent == "confirmation":
        return "exercise_generate"  # User confirmed, generate actual exercise
    elif intent == "answer":
        return "correction"
    else:
        return "feedback"


def feedback_node(state: AgentState) -> dict:
    """Generate pedagogical response."""
    question = state.get("user_message", "")
    context = state.get("context", [])
    correction = state.get("correction")

    response = generate_feedback(
        question=question,
        context=context,
        correction=correction,
    )

    return {"response": response}


def exercise_proposal_node(state: AgentState) -> dict:
    """Return exercise proposal for user confirmation."""
    proposal = state.get("exercise_proposal")

    # If no proposal (user wants to modify), ask for preferences
    if not proposal:
        response = "Quel type d'exercice souhaitez-vous ?"
        # Return special metadata for frontend to show type selection card
        return {
            "response": response,
            "exercise_type_selection": True,
        }

    # Format type label
    type_labels = {
        "qcm": "QCM (Quiz à choix multiples)",
        "code": "Exercice de code",
        "open": "Question ouverte",
    }
    type_label = type_labels.get(proposal.get("type", "open"), "Exercice")

    difficulty_labels = {
        "easy": "Facile",
        "medium": "Intermédiaire",
        "hard": "Difficile",
    }
    difficulty_label = difficulty_labels.get(proposal.get("difficulty", "medium"), "Intermédiaire")

    # Response with proposal details - this will be detected by frontend
    response = (
        f"📋 **Exercice proposé**\n\n"
        f"**Type:** {type_label}\n"
        f"**Sujet:** {proposal.get('topic', 'Général')}\n"
        f"**Difficulté:** {difficulty_label}\n"
    )

    if proposal.get("type") == "qcm":
        response += f"**Questions:** {proposal.get('num_questions', 5)}\n"

    response += "\n*Voulez-vous générer cet exercice ? (Oui/Non/Modifier)*"

    return {"response": response}


def exercise_generate_node(state: AgentState) -> dict:
    """Generate actual exercise after user confirmation."""
    proposal = state.get("exercise_proposal", {})
    context = state.get("context", [])
    conversation_history = state.get("conversation_history", [])
    student_level = state.get("student_level", 0.5)
    history = state.get("history", [])
    session_id = state.get("session_id", "default")

    exercise_type = proposal.get("type", "open")
    topic = proposal.get("topic", "")
    difficulty = proposal.get("difficulty", "medium")
    num_questions = proposal.get("num_questions", 5)

    # Build enriched context from RAG + conversation
    enriched_context = context.copy()
    if conversation_history:
        # Add recent conversation as context
        conv_summary = "\n".join([
            f"{msg['role']}: {msg['content'][:200]}"
            for msg in conversation_history[-5:]  # Last 5 messages
        ])
        enriched_context.insert(0, f"Recent conversation:\n{conv_summary}")

    if exercise_type == "qcm":
        # Use QCM generation logic with context
        from app.services.ai.qcm_workflow import run_generate_qcm

        questions = run_generate_qcm(
            session_id=session_id,
            topic=topic,
            num_questions=num_questions,
            difficulty=difficulty,
            student_level=student_level,
            context=enriched_context,  # Pass context to QCM generation
        )

        exercise = {
            "type": "qcm",
            "topic": topic,
            "difficulty": difficulty,
            "questions": questions,
            "num_questions": len(questions),
        }

        # Format response for QCM
        response = f"📝 **{topic}** - QCM ({len(questions)} questions)\n\n"
        for i, q in enumerate(questions, 1):
            response += f"**Q{i}.** {q['question_text']}\n"
            for opt in q.get("options", []):
                response += f"  {opt['label']}) {opt['text']}\n"
            response += "\n"

        response += "*Répondez en indiquant les lettres (ex: A, B, C, D, A)*"

    elif exercise_type == "code":
        # Generate code exercise
        exercise = generate_exercise(
            topic=topic,
            difficulty=difficulty,
            context=enriched_context,
            student_level=student_level,
            history=history,
            exercise_type="code",
        )
        exercise["type"] = "code"

        response = f"💻 **Exercice de code: {topic}**\n\n"
        response += f"{exercise['question']}\n\n"
        if exercise.get("hints"):
            response += "💡 *Des indices sont disponibles si besoin.*\n\n"
        response += "*Envoyez votre code en réponse.*"

    else:  # open
        exercise = generate_exercise(
            topic=topic,
            difficulty=difficulty,
            context=enriched_context,
            student_level=student_level,
            history=history,
        )
        exercise["type"] = "open"

        response = f"📝 **Exercice: {topic}**\n\n"
        response += f"{exercise['question']}\n\n"
        if exercise.get("hints"):
            response += "💡 *Des indices sont disponibles si besoin.*"

    return {
        "current_exercise": exercise,
        "exercise_proposal": None,  # Clear proposal
        "response": response,
    }


def correction_node(state: AgentState) -> dict:
    """Correct student answer based on exercise type."""
    exercise = state.get("current_exercise", {})
    student_answer = state.get("student_answer", "")
    context = state.get("context", [])
    student_level = state.get("student_level", 0.5)
    session_id = state.get("session_id", "default")
    exercise_type = exercise.get("type", "open")

    if exercise_type == "qcm":
        # Use QCM-specific correction flow
        import json as json_module
        from app.services.ai.qcm_workflow import run_submit_qcm

        # Parse student answers - handle JSON array, comma-separated, or direct letters
        questions = exercise.get("questions", [])
        raw_answers = student_answer.strip()

        # Try to parse as JSON array first (e.g., '["A","B","C","D","A"]')
        try:
            parsed = json_module.loads(raw_answers)
            if isinstance(parsed, list):
                student_answers = [str(a).strip().upper() for a in parsed]
            else:
                student_answers = [str(parsed).strip().upper()]
        except (json_module.JSONDecodeError, ValueError):
            # Not JSON, try other formats
            raw_answers = raw_answers.replace(" ", "").upper()

            # Handle comma-separated (e.g., "A,B,C,D,A")
            if "," in raw_answers:
                student_answers = [a.strip() for a in raw_answers.split(",") if a.strip()]
            else:
                # Direct sequence like "ABCDA"
                student_answers = list(raw_answers)

        # Ensure we have an answer for each question
        while len(student_answers) < len(questions):
            student_answers.append("")

        result = run_submit_qcm(
            session_id=session_id,
            topic=exercise.get("topic", ""),
            questions=questions,
            student_answers=student_answers,
            student_level=student_level,
        )

        # Build correction result from QCM result
        corrected_questions = result.get("corrected_questions", [])
        grade_report = result.get("grade_report", {})

        correct_count = sum(1 for q in corrected_questions if q.get("is_correct"))
        total = len(corrected_questions)
        score = correct_count / total if total > 0 else 0.0

        correction = {
            "is_correct": score >= 0.5,
            "score": score,
            "correct_count": correct_count,
            "total_questions": total,
            "errors": grade_report.get("weak_points", []),
            "feedback_hints": grade_report.get("recommendations", []),
            "updated_level": result.get("updated_level", student_level),
            "verdict": grade_report.get("grade_label", "Insuffisant"),
            "grade_letter": grade_report.get("grade_letter", "F"),
            "summary": grade_report.get("summary", ""),
            "strong_points": grade_report.get("strong_points", []),
            "corrected_questions": corrected_questions,
        }

    else:
        # Use generic correction for open/code exercises
        correction = correct_answer(
            exercise=exercise,
            student_answer=student_answer,
            context=context,
            student_level=student_level,
            session_id=session_id,
        )

    return {
        "correction": correction,
        "updated_level": correction.get("updated_level", student_level),
    }


def post_correction_feedback_node(state: AgentState) -> dict:
    """Generate feedback after correction."""
    question = state.get("current_exercise", {}).get("question", "")
    context = state.get("context", [])
    correction = state.get("correction")

    response = generate_feedback(
        question=question,
        context=context,
        correction=correction,
    )

    return {"response": response}


# ═══════════════════════════════════════════════════════════════════════════════
# WORKFLOW GRAPH
# ═══════════════════════════════════════════════════════════════════════════════


def build_workflow() -> StateGraph:
    """
    Build and compile the multi-agent workflow.

    Flow:
        START → RAG → Router → [Feedback|ExerciseProposal|ExerciseGenerate|Correction] → END
                                     ↓
                              Post-Correction Feedback → END
    """
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("rag", rag_node)
    graph.add_node("router", router_node)
    graph.add_node("feedback", feedback_node)
    graph.add_node("exercise_proposal", exercise_proposal_node)
    graph.add_node("exercise_generate", exercise_generate_node)
    graph.add_node("correction", correction_node)
    graph.add_node("post_correction_feedback", post_correction_feedback_node)

    # Set entry point
    graph.set_entry_point("rag")

    # RAG → Router
    graph.add_edge("rag", "router")

    # Router → conditional routing
    graph.add_conditional_edges(
        "router",
        route_by_intent,
        {
            "feedback": "feedback",
            "exercise_proposal": "exercise_proposal",
            "exercise_generate": "exercise_generate",
            "correction": "correction",
        },
    )

    # Terminal edges
    graph.add_edge("feedback", END)
    graph.add_edge("exercise_proposal", END)
    graph.add_edge("exercise_generate", END)

    # Correction → Post-correction feedback → End
    graph.add_edge("correction", "post_correction_feedback")
    graph.add_edge("post_correction_feedback", END)

    return graph.compile()


# Compiled workflow (singleton)
workflow = build_workflow()


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════════


def create_initial_state(
    session_id: str,
    user_message: str,
    student_level: float = 0.5,
    history: Optional[list[dict]] = None,
    conversation_history: Optional[list[dict]] = None,
    current_exercise: Optional[dict] = None,
    exercise_proposal: Optional[dict] = None,
) -> AgentState:
    """
    Create an initial state for the workflow.

    Args:
        session_id: Unique session identifier.
        user_message: The user's input message.
        student_level: Current student level (0.0-1.0).
        history: Previous exercise history.
        conversation_history: Recent chat messages for context.
        current_exercise: Ongoing exercise (if any).
        exercise_proposal: Pending exercise proposal (if any).

    Returns:
        AgentState ready for workflow.invoke().
    """
    return AgentState(
        session_id=session_id,
        collection_name=f"session_{session_id}",
        user_message=user_message,
        student_level=student_level,
        history=history or [],
        conversation_history=conversation_history or [],
        context=[],
        exercise_proposal=exercise_proposal,
        exercise_type=None,
        current_exercise=current_exercise,
        student_answer=None,
        correction=None,
        response=None,
        intent=None,
        updated_level=None,
    )


def chat(
    session_id: str,
    message: str,
    student_level: float = 0.5,
    history: Optional[list[dict]] = None,
    conversation_history: Optional[list[dict]] = None,
    current_exercise: Optional[dict] = None,
    exercise_proposal: Optional[dict] = None,
    confirm_exercise: bool = False,
    submit_exercise: bool = False,
) -> dict:
    """
    Main entry point for the chat workflow.

    Args:
        session_id: Unique session identifier.
        message: User's message.
        student_level: Current student level (0.0-1.0).
        history: Previous exercise history.
        conversation_history: Recent chat messages for context.
        current_exercise: Ongoing exercise (if any).
        exercise_proposal: Pending exercise proposal (if any).
        confirm_exercise: Whether user is confirming an exercise proposal.
        submit_exercise: Whether user is submitting an exercise answer.

    Returns:
        Final state dict with response, updated_level, current_exercise, exercise_proposal, etc.
    """
    initial_state = create_initial_state(
        session_id=session_id,
        user_message=message,
        student_level=student_level,
        history=history,
        conversation_history=conversation_history,
        current_exercise=current_exercise,
        exercise_proposal=exercise_proposal,
    )

    # Override intent if explicit action from frontend
    if confirm_exercise and exercise_proposal:
        initial_state["intent"] = "confirmation"
    elif submit_exercise and current_exercise:
        initial_state["intent"] = "answer"
        initial_state["student_answer"] = message

    result = workflow.invoke(initial_state)
    return result
