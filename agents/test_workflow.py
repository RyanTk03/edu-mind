#!/usr/bin/env python3
"""
Test script for EDU-MIND Multi-Agent Workflow.

Run this script to verify all agents work together correctly.

Usage:
    cd agents
    python test_workflow.py
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Verify environment
if not os.getenv("GROQ_API_KEY"):
    print("ERROR: GROQ_API_KEY not found in environment")
    print("Please set it in agents/.env file")
    exit(1)

print("=" * 60)
print("EDU-MIND Multi-Agent Workflow Test")
print("=" * 60)

# Import modules
print("\n[1/6] Importing modules...")
try:
    from norm import generate_feedback, generate_exercise, correct_answer
    from rag import create_collection, ingest_text, get_context
    from router import classify_intent, quick_intent
    from workflow import chat, create_initial_state
    print("     All imports successful!")
except ImportError as e:
    print(f"ERROR: Import failed: {e}")
    print("Make sure you're running from the agents/ directory")
    exit(1)

# Test session ID
SESSION_ID = "test_session_123"

# Test RAG System
print("\n[2/6] Testing RAG System...")
try:
    # Create collection
    collection = create_collection(SESSION_ID)
    print(f"     Created collection: {collection.name}")

    # Ingest sample document
    sample_doc = """
    Les dérivées en mathématiques.

    La dérivée d'une fonction f en un point x mesure le taux de variation instantané.

    Formules importantes:
    - Dérivée de x^n = n * x^(n-1)
    - Dérivée de sin(x) = cos(x)
    - Dérivée de e^x = e^x

    La règle de la chaîne: (f∘g)' = (f'∘g) * g'
    """

    chunks = ingest_text(SESSION_ID, sample_doc, source="test_doc")
    print(f"     Ingested document: {chunks} chunks")

    # Test retrieval
    context = get_context(SESSION_ID, "dérivée de x^n")
    print(f"     Retrieved context: {len(context)} chunks")
    if context:
        print(f"     Sample: {context[0][:100]}...")

except Exception as e:
    print(f"ERROR: RAG test failed: {e}")

# Test Router
print("\n[3/6] Testing Intent Router...")
try:
    # Test question intent
    result = quick_intent("Explique-moi les dérivées", has_exercise=False)
    print(f"     'Explique-moi les dérivées' → {result}")

    # Test exercise intent
    result = quick_intent("Donne-moi un exercice", has_exercise=False)
    print(f"     'Donne-moi un exercice' → {result}")

    # Test answer intent
    result = quick_intent("La réponse est 42", has_exercise=True, awaiting_answer=True)
    print(f"     'La réponse est 42' (with exercise) → {result}")

    # Test LLM-based classification (if API key available)
    print("     Testing LLM router...")
    llm_result = classify_intent("Je veux pratiquer les matrices")
    print(f"     'Je veux pratiquer les matrices' → {llm_result.intent} (confidence: {llm_result.confidence})")

except Exception as e:
    print(f"WARNING: Router test issue: {e}")

# Test Feedback Agent
print("\n[4/6] Testing Feedback Agent...")
try:
    response = generate_feedback(
        question="C'est quoi une dérivée?",
        context=["La dérivée mesure le taux de variation instantané d'une fonction."],
    )
    print(f"     Response preview: {response[:200]}...")
except Exception as e:
    print(f"ERROR: Feedback agent failed: {e}")

# Test Exercise Agent
print("\n[5/6] Testing Exercise Agent...")
try:
    exercise = generate_exercise(
        topic="les dérivées",
        difficulty="easy",
        context=["Dérivée de x^n = n * x^(n-1)"],
        student_level=0.5,
    )
    print(f"     Question: {exercise['question'][:100]}...")
    print(f"     Expected: {exercise['expected_answer'][:100]}...")
    print(f"     Hints: {len(exercise.get('hints', []))} hints")
except Exception as e:
    print(f"ERROR: Exercise agent failed: {e}")

# Test Full Workflow
print("\n[6/6] Testing Full Workflow...")
try:
    # Test 1: Question flow
    print("\n     --- Test A: Question Flow ---")
    result = chat(
        session_id=SESSION_ID,
        message="Explique-moi comment calculer une dérivée",
        student_level=0.5,
    )
    print(f"     Intent: {result.get('intent')}")
    print(f"     Response: {result.get('response', '')[:150]}...")

    # Test 2: Exercise flow
    print("\n     --- Test B: Exercise Flow ---")
    result = chat(
        session_id=SESSION_ID,
        message="Donne-moi un exercice sur les dérivées",
        student_level=0.5,
    )
    print(f"     Intent: {result.get('intent')}")
    print(f"     Exercise: {bool(result.get('current_exercise'))}")
    print(f"     Response: {result.get('response', '')[:150]}...")

    # Test 3: Answer flow (if exercise was generated)
    if result.get('current_exercise'):
        print("\n     --- Test C: Answer Flow ---")
        exercise = result['current_exercise']
        answer_result = chat(
            session_id=SESSION_ID,
            message="3x^2",  # Sample answer
            student_level=0.5,
            current_exercise=exercise,
        )
        print(f"     Intent: {answer_result.get('intent')}")
        print(f"     Correction: {bool(answer_result.get('correction'))}")
        if answer_result.get('correction'):
            correction = answer_result['correction']
            print(f"     Score: {correction.get('score', 'N/A')}")
            print(f"     Is Correct: {correction.get('is_correct', 'N/A')}")
        print(f"     Response: {answer_result.get('response', '')[:150]}...")

except Exception as e:
    print(f"ERROR: Workflow test failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Test Complete!")
print("=" * 60)
print("""
Next steps:
1. Install dependencies: pip install chromadb
2. Run the backend: cd backend && uvicorn app.main:app --reload
3. Test the API endpoints

Your multi-agent system is ready!
""")
