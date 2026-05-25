"""Message-related schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.message import MessageRole


class MessageCreate(BaseModel):
    """Schema for creating a message."""

    content: str = Field(min_length=1, max_length=10000)


class MessageResponse(BaseModel):
    """Schema for message response."""

    id: str
    session_id: str
    role: MessageRole
    content: str
    created_at: datetime
    metadata: dict

    class Config:
        from_attributes = True


class ChatHistoryResponse(BaseModel):
    """Schema for chat history response."""

    messages: list[MessageResponse]
    total: int
