"""Session-related schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SessionCreate(BaseModel):
    """Schema for creating a session."""

    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)


class SessionUpdate(BaseModel):
    """Schema for updating a session."""

    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)


class SessionResponse(BaseModel):
    """Schema for session response."""

    id: str
    user_id: str
    title: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    attachment_count: int = 0
    message_count: int = 0
    exercise_count: int = 0

    class Config:
        from_attributes = True


class SessionListResponse(BaseModel):
    """Schema for list of sessions."""

    sessions: list[SessionResponse]
    total: int
