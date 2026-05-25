"""Fallback local implementations."""
import sys
from pathlib import Path

# Add repo root to path
repo_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(repo_root))

# Now import from agents
from agents.qcm_agents import (
    generate_qcm,
    correct_qcm,
    evaluate_grade,
)
from agents.orchestrator import (
    generate_qcm_workflow,
    submit_qcm_answers_workflow,
    get_workflow_graph_metadata,
)
from agents.rag import get_context