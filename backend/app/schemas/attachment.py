"""Attachment-related schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AttachmentResponse(BaseModel):
    """Schema for attachment response."""

    id: str
    session_id: str
    filename: str
    original_filename: str
    file_type: str
    file_size: int
    uploaded_at: datetime
    is_processed: bool
    chunk_count: int
    processing_error: Optional[str]

    class Config:
        from_attributes = True


class AttachmentStatusResponse(BaseModel):
    """Schema for attachment processing status."""

    id: str
    is_processed: bool
    chunk_count: int
    processing_error: Optional[str]
