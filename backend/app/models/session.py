from datetime import datetime
from typing import Optional

from beanie import Document, Indexed, Link
from pydantic import Field

from app.models.user import User


class Session(Document):
    """Study session - like a NotebookLM notebook."""

    user: Link[User]
    title: Indexed(str)
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "sessions"
