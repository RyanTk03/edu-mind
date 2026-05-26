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
    metadata: dict = Field(default_factory=dict)  # For AI state (current_exercise, history)
    # Per-session progress tracking
    progress_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    exercises_completed: int = Field(default=0)
    level_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)

    class Settings:
        name = "sessions"
