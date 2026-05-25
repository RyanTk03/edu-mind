"""Attachment upload/download endpoints."""

import os
import uuid
from pathlib import Path

import aiofiles
from beanie import PydanticObjectId
from fastapi import APIRouter, BackgroundTasks, File, UploadFile
from fastapi.responses import FileResponse

from app.config import settings
from app.core.deps import CurrentUser
from app.core.exceptions import (
    FileTooLargeError,
    ForbiddenError,
    NotFoundError,
    UnsupportedFileTypeError,
)
from app.models.attachment import Attachment
from app.models.session import Session
from app.schemas.attachment import AttachmentResponse, AttachmentStatusResponse
from app.services.ai_service import AIService

router = APIRouter(prefix="/sessions/{session_id}/attachments", tags=["Attachments"])

ALLOWED_TYPES = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/msword": ".doc",
    "text/plain": ".txt",
    "text/markdown": ".md",
}


async def process_attachment_for_rag(
    attachment_id: str,
    session_id: str,
    file_path: str,
    file_type: str,
    original_filename: str,
):
    """Background task to process attachment and ingest into RAG."""
    try:
        attachment = await Attachment.get(PydanticObjectId(attachment_id))
        if not attachment:
            return

        chunk_count = 0

        if file_type == "application/pdf":
            # Ingest PDF using AI service
            chunk_count = await AIService.ingest_pdf_file(
                session_id=session_id,
                pdf_path=file_path,
                metadata={"filename": original_filename},
            )
        elif file_type in ("text/plain", "text/markdown"):
            # Read and ingest text file
            async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                content = await f.read()
            chunk_count = await AIService.ingest_document(
                session_id=session_id,
                content=content,
                source=original_filename,
            )
        # TODO: Add support for DOCX files

        # Update attachment status
        attachment.is_processed = True
        attachment.chunk_count = chunk_count
        await attachment.save()

    except Exception as e:
        # Update attachment with error
        if attachment:
            attachment.is_processed = False
            attachment.processing_error = str(e)
            await attachment.save()


async def verify_session_ownership(
    session_id: str, current_user: CurrentUser
) -> Session:
    """Verify session exists and belongs to current user."""
    try:
        session = await Session.get(PydanticObjectId(session_id))
    except Exception:
        raise NotFoundError("Session not found")

    if not session:
        raise NotFoundError("Session not found")

    if session.user.ref.id != current_user.id:
        raise ForbiddenError("Not your session")

    return session


def attachment_to_response(attachment: Attachment) -> AttachmentResponse:
    """Convert attachment model to response schema."""
    return AttachmentResponse(
        id=str(attachment.id),
        session_id=str(attachment.session.ref.id),
        filename=attachment.filename,
        original_filename=attachment.original_filename,
        file_type=attachment.file_type,
        file_size=attachment.file_size,
        uploaded_at=attachment.uploaded_at,
        is_processed=attachment.is_processed,
        chunk_count=attachment.chunk_count,
        processing_error=attachment.processing_error,
    )


@router.get("/", response_model=list[AttachmentResponse])
async def list_attachments(session_id: str, current_user: CurrentUser):
    """List all attachments for a session."""
    session = await verify_session_ownership(session_id, current_user)

    attachments = await Attachment.find(
        Attachment.session.id == session.id
    ).to_list()

    return [attachment_to_response(a) for a in attachments]


@router.post("/", response_model=AttachmentResponse)
async def upload_attachment(
    session_id: str,
    current_user: CurrentUser,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    """Upload a file attachment to a session and process for RAG."""
    session = await verify_session_ownership(session_id, current_user)

    # Validate file type
    if file.content_type not in ALLOWED_TYPES:
        raise UnsupportedFileTypeError(
            f"File type {file.content_type} not supported. Allowed: PDF, DOCX, DOC, TXT, MD"
        )

    # Read file content to check size
    content = await file.read()
    file_size = len(content)

    max_size = settings.max_upload_size_mb * 1024 * 1024
    if file_size > max_size:
        raise FileTooLargeError(
            f"File too large. Maximum size: {settings.max_upload_size_mb}MB"
        )

    # Create upload directory if needed
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Generate unique filename
    ext = ALLOWED_TYPES[file.content_type]
    unique_filename = f"{uuid.uuid4()}{ext}"
    file_path = upload_dir / unique_filename

    # Save file
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    # Create attachment record
    attachment = Attachment(
        session=session,
        filename=unique_filename,
        original_filename=file.filename or "unknown",
        file_type=file.content_type,
        file_size=file_size,
        file_path=str(file_path),
        is_processed=False,
    )
    await attachment.insert()

    # Process document in background for RAG ingestion
    background_tasks.add_task(
        process_attachment_for_rag,
        attachment_id=str(attachment.id),
        session_id=session_id,
        file_path=str(file_path),
        file_type=file.content_type,
        original_filename=file.filename or "unknown",
    )

    return attachment_to_response(attachment)


@router.get("/{attachment_id}", response_model=AttachmentResponse)
async def get_attachment(
    session_id: str, attachment_id: str, current_user: CurrentUser
):
    """Get attachment info."""
    session = await verify_session_ownership(session_id, current_user)

    try:
        attachment = await Attachment.get(PydanticObjectId(attachment_id))
    except Exception:
        raise NotFoundError("Attachment not found")

    if not attachment:
        raise NotFoundError("Attachment not found")

    if attachment.session.ref.id != session.id:
        raise ForbiddenError("Attachment doesn't belong to this session")

    return attachment_to_response(attachment)


@router.get("/{attachment_id}/download")
async def download_attachment(
    session_id: str, attachment_id: str, current_user: CurrentUser
):
    """Download the actual file."""
    session = await verify_session_ownership(session_id, current_user)

    try:
        attachment = await Attachment.get(PydanticObjectId(attachment_id))
    except Exception:
        raise NotFoundError("Attachment not found")

    if not attachment:
        raise NotFoundError("Attachment not found")

    if attachment.session.ref.id != session.id:
        raise ForbiddenError("Attachment doesn't belong to this session")

    if not os.path.exists(attachment.file_path):
        raise NotFoundError("File not found on disk")

    return FileResponse(
        path=attachment.file_path,
        filename=attachment.original_filename,
        media_type=attachment.file_type,
    )


@router.delete("/{attachment_id}")
async def delete_attachment(
    session_id: str, attachment_id: str, current_user: CurrentUser
):
    """Delete an attachment."""
    session = await verify_session_ownership(session_id, current_user)

    try:
        attachment = await Attachment.get(PydanticObjectId(attachment_id))
    except Exception:
        raise NotFoundError("Attachment not found")

    if not attachment:
        raise NotFoundError("Attachment not found")

    if attachment.session.ref.id != session.id:
        raise ForbiddenError("Attachment doesn't belong to this session")

    # Delete file from disk
    if os.path.exists(attachment.file_path):
        os.remove(attachment.file_path)

    # TODO: Delete vectors from ChromaDB (AI agent integration later)

    await attachment.delete()

    return {"message": "Attachment deleted successfully"}


@router.get("/{attachment_id}/status", response_model=AttachmentStatusResponse)
async def get_attachment_status(
    session_id: str, attachment_id: str, current_user: CurrentUser
):
    """Check attachment processing status."""
    session = await verify_session_ownership(session_id, current_user)

    try:
        attachment = await Attachment.get(PydanticObjectId(attachment_id))
    except Exception:
        raise NotFoundError("Attachment not found")

    if not attachment:
        raise NotFoundError("Attachment not found")

    if attachment.session.ref.id != session.id:
        raise ForbiddenError("Attachment doesn't belong to this session")

    return AttachmentStatusResponse(
        id=str(attachment.id),
        is_processed=attachment.is_processed,
        chunk_count=attachment.chunk_count,
        processing_error=attachment.processing_error,
    )
