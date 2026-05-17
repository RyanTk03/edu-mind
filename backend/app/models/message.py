from datetime import datetime
from enum import Enum
from typing import Optional

from beanie import Document, Indexed, Link
from pydantic import Field

from app.models.session import Session


class MessageRole(str, Enum):
    """Who sent the message."""

    USER = "user"
    AI = "ai"


class Message(Document):
    """Chat message in a session."""

    session: Link[Session]
    role: MessageRole
    content: str
    created_at: Indexed(datetime) = Field(default_factory=datetime.utcnow)

    # Optional metadata (e.g., sources used for AI response)
    metadata: dict = Field(default_factory=dict)

    class Settings:
        name = "messages"
