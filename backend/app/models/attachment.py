from datetime import datetime
from typing import Optional

from beanie import Document, Indexed, Link
from pydantic import Field

from app.models.session import Session


class Attachment(Document):
    """File attachment uploaded to a session."""

    session: Link[Session]
    filename: str
    original_filename: str
    file_type: str  # MIME type
    file_size: int  # bytes
    file_path: str  # local storage path
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)

    # Processing status
    is_processed: bool = False
    chunk_count: int = 0
    processing_error: Optional[str] = None

    class Settings:
        name = "attachments"
