from fastapi import APIRouter

router = APIRouter(prefix="/sessions/{session_id}/chat", tags=["Chat"])

@router.get("/")
async def get_chat_history(session_id: str):
    return None

@router.post("/")
async def send_message(session_id: str):
    return None

@router.delete("/")
async def clear_chat_history(session_id: str):
    return None
