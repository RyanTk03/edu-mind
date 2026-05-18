from fastapi import APIRouter

router = APIRouter(prefix="/sessions/{session_id}/exercises", tags=["Exercises"])

@router.get("/")
async def list_exercises(session_id: str):
    return None

@router.post("/generate")
async def generate_exercise(session_id: str):
    return None

@router.get("/{exercise_id}")
async def get_exercise(session_id: str, exercise_id: str):
    return None

@router.post("/{exercise_id}/submit")
async def submit_exercise(session_id: str, exercise_id: str):
    return None

@router.get("/{exercise_id}/results")
async def get_exercise_results(session_id: str, exercise_id: str):
    return None
