from fastapi import APIRouter, UploadFile, File

router = APIRouter(prefix="/sessions/{session_id}/attachments", tags=["Attachments"])

@router.get("/")
async def list_attachments(session_id: str):
    return None

@router.post("/")
async def upload_attachment(session_id: str, file: UploadFile = File(...)):
    return None

@router.get("/{attachment_id}")
async def get_attachment(session_id: str, attachment_id: str):
    return None

@router.delete("/{attachment_id}")
async def delete_attachment(session_id: str, attachment_id: str):
    return None

@router.get("/{attachment_id}/status")
async def get_attachment_status(session_id: str, attachment_id: str):
    return None
