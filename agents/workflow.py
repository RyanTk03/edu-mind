"""
Multi-Agent Orchestration Workflow for EDU-MIND.

Uses LangGraph to coordinate RAG, Router, and all three agents.
"""

from typing import Literal, Optional

from langgraph.graph import StateGraph, END

from .norm import AgentState, generate_feedback, generate_exercise, correct_answer
from .rag import get_context
from .router import classify_intent, quick_intent


# ── Node Functions ───────────────────────────────────────────────────────────


def rag_node(state: AgentState) -> dict:
    """
    Retrieve relevant context from ChromaDB.

    This node fetches documents relevant to the user's message
    to provide context for the other agents.
    """
    session_id = state.get("session_id", "default")
    user_message = state.get("user_message", "")

    # Get context from RAG
    context = get_context(
        session_id=session_id,
        query=user_message,
        k=5,
    )

    return {"context": context}


def router_node(state: AgentState) -> dict:
    """
    Classify user intent using LLM router.

    Determines if the user wants to:
    - Ask a question (→ feedback agent)
    - Request an exercise (→ exercise agent)
    - Submit an answer (→ correction agent)
    """
    user_message = state.get("user_message", "")
    current_exercise = state.get("current_exercise")
    correction = state.get("correction")

    has_exercise = current_exercise is not None
    awaiting_answer = has_exercise and correction is None

    try:
        # Use LLM-based classification
        result = classify_intent(
            user_message=user_message,
            has_exercise=has_exercise,
            awaiting_answer=awaiting_answer,
        )
        intent = result.intent
    except Exception:
        # Fallback to rule-based classification
        intent = quick_intent(
            user_message=user_message,
            has_exercise=has_exercise,
            awaiting_answer=awaiting_answer,
        )

    # If intent is "answer", extract the student answer
    updates = {"intent": intent}
    if intent == "answer":
        updates["student_answer"] = user_message

    return updates


def route_by_intent(state: AgentState) -> str:
    """
    Route to the appropriate agent based on classified intent.

    Returns the name of the next node to execute.
    """
    intent = state.get("intent", "question")

    if intent == "exercise":
        return "exercise"
    elif intent == "answer":
        return "correction"
    else:
        return "feedback"


def feedback_node(state: AgentState) -> dict:
    """
    Generate pedagogical response using the Feedback Agent.
    """
    question = state.get("user_message", "")
    context = state.get("context", [])
    correction = state.get("correction")

    response = generate_feedback(
        question=question,
        context=context,
        correction=correction,
    )

    return {"response": response}


def exercise_node(state: AgentState) -> dict:
    """
    Generate an exercise using the Exercise Agent.
    """
    topic = state.get("user_message", "")
    context = state.get("context", [])
    student_level = state.get("student_level", 0.5)
    history = state.get("history", [])

    # Determine difficulty based on student level
    if student_level < 0.35:
        difficulty = "easy"
    elif student_level < 0.65:
        difficulty = "medium"
    else:
        difficulty = "hard"

    exercise = generate_exercise(
        topic=topic,
        difficulty=difficulty,
        context=context,
        student_level=student_level,
        history=history,
    )

    # Format response with the exercise question
    response = f"**Exercice:**\n\n{exercise['question']}"
    if exercise.get("hints"):
        response += "\n\n💡 *Des indices sont disponibles si besoin.*"

    return {
        "current_exercise": exercise,
        "response": response,
    }


def correction_node(state: AgentState) -> dict:
    """
    Correct student answer using the Correction Agent.
    """
    exercise = state.get("current_exercise", {})
    student_answer = state.get("student_answer", "")
    context = state.get("context", [])
    student_level = state.get("student_level", 0.5)
    session_id = state.get("session_id", "default")

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
    """
    Generate feedback after correction.

    Always provides pedagogical feedback after correcting an answer,
    explaining what was right/wrong and helping the student understand.
    """
    question = state.get("current_exercise", {}).get("question", "")
    context = state.get("context", [])
    correction = state.get("correction")

    response = generate_feedback(
        question=question,
        context=context,
        correction=correction,
    )

    return {"response": response}


# ── Build the Workflow Graph ─────────────────────────────────────────────────


def build_workflow() -> StateGraph:
    """
    Build and compile the multi-agent workflow.

    Workflow structure:
        ┌─────────┐
        │  START  │
        └────┬────┘
             │
        ┌────▼────┐
        │   RAG   │  ← Retrieve context
        └────┬────┘
             │
        ┌────▼────┐
        │ ROUTER  │  ← Classify intent
        └────┬────┘
             │
       ┌─────┴─────┬──────────────┐
       │           │              │
       ▼           ▼              ▼
    question    exercise       answer
       │           │              │
       ▼           ▼              ▼
    ┌──────┐  ┌────────┐   ┌───────────┐
    │FEEDBK│  │EXERCISE│   │CORRECTION │
    └──┬───┘  └────┬───┘   └─────┬─────┘
       │           │             │
       │           │       ┌─────▼─────┐
       │           │       │POST_FEEDBK│
       │           │       └─────┬─────┘
       │           │             │
       └───────────┴─────────────┘
                   │
              ┌────▼────┐
              │   END   │
              └─────────┘
    """
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("rag", rag_node)
    graph.add_node("router", router_node)
    graph.add_node("feedback", feedback_node)
    graph.add_node("exercise", exercise_node)
    graph.add_node("correction", correction_node)
    graph.add_node("post_correction_feedback", post_correction_feedback_node)

    # Set entry point
    graph.set_entry_point("rag")

    # RAG → Router
    graph.add_edge("rag", "router")

    # Router → conditional routing based on intent
    graph.add_conditional_edges(
        "router",
        route_by_intent,
        {
            "feedback": "feedback",
            "exercise": "exercise",
            "correction": "correction",
        },
    )

    # Terminal edges
    graph.add_edge("feedback", END)
    graph.add_edge("exercise", END)

    # Correction → Post-correction feedback → End
    graph.add_edge("correction", "post_correction_feedback")
    graph.add_edge("post_correction_feedback", END)

    return graph.compile()


# ── Compiled Workflow (Singleton) ────────────────────────────────────────────
workflow = build_workflow()


# ── Convenience Functions ────────────────────────────────────────────────────


def create_initial_state(
    session_id: str,
    user_message: str,
    student_level: float = 0.5,
    history: Optional[list[dict]] = None,
    current_exercise: Optional[dict] = None,
) -> AgentState:
    """
    Create an initial state for the workflow.

    Args:
        session_id: Unique session identifier.
        user_message: The user's input message.
        student_level: Current student level (0.0-1.0).
        history: Previous exercise history.
        current_exercise: Ongoing exercise (if any).

    Returns:
        AgentState ready to be passed to workflow.invoke().
    """
    return AgentState(
        session_id=session_id,
        collection_name=f"session_{session_id}",
        user_message=user_message,
        student_level=student_level,
        history=history or [],
        context=[],
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
    current_exercise: Optional[dict] = None,
) -> dict:
    """
    Main entry point for the chat workflow.

    This is what the backend calls to process a user message.

    Args:
        session_id: Unique session identifier.
        message: User's message.
        student_level: Current student level (0.0-1.0).
        history: Previous exercise history.
        current_exercise: Ongoing exercise (if any).

    Returns:
        Final state dict with response, updated_level, current_exercise, etc.
    """
    initial_state = create_initial_state(
        session_id=session_id,
        user_message=message,
        student_level=student_level,
        history=history,
        current_exercise=current_exercise,
    )

    result = workflow.invoke(initial_state)

    return result
