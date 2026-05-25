"""Pydantic schemas for request/response DTOs."""

from app.schemas.user import (
    UserCreate,
    UserLogin,
    UserResponse,
    UserProfileResponse,
    UserProfileUpdate,
    TokenResponse,
    TokenRefresh,
)
from app.schemas.session import (
    SessionCreate,
    SessionUpdate,
    SessionResponse,
    SessionListResponse,
)
from app.schemas.attachment import (
    AttachmentResponse,
    AttachmentStatusResponse,
)
from app.schemas.message import (
    MessageCreate,
    MessageResponse,
    ChatHistoryResponse,
)
from app.schemas.exercise import (
    ExerciseGenerateRequest,
    ExerciseResponse,
    ExerciseSubmitRequest,
    ExerciseResultsResponse,
    QuestionResponse,
)

__all__ = [
    # User
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "UserProfileResponse",
    "UserProfileUpdate",
    "TokenResponse",
    "TokenRefresh",
    # Session
    "SessionCreate",
    "SessionUpdate",
    "SessionResponse",
    "SessionListResponse",
    # Attachment
    "AttachmentResponse",
    "AttachmentStatusResponse",
    # Message
    "MessageCreate",
    "MessageResponse",
    "ChatHistoryResponse",
    # Exercise
    "ExerciseGenerateRequest",
    "ExerciseResponse",
    "ExerciseSubmitRequest",
    "ExerciseResultsResponse",
    "QuestionResponse",
]
