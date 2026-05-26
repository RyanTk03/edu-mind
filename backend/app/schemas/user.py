"""User-related schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.models.user import LearnerLevel


class UserCreate(BaseModel):
    """Schema for user registration."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=100)
    name: str = Field(min_length=1, max_length=100)


class UserLogin(BaseModel):
    """Schema for user login."""

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for user response (public info)."""

    id: str
    email: EmailStr
    name: str
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Schema for JWT token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    """Schema for token refresh request."""

    refresh_token: str


class UserProfileResponse(BaseModel):
    """Schema for user profile response."""

    id: str
    user_id: str
    level: LearnerLevel
    level_score: Optional[float]  # None = not assessed yet
    exercises_completed: int
    weak_points: list[str]
    strong_points: list[str]
    preferences: dict

    class Config:
        from_attributes = True


class UserProfileUpdate(BaseModel):
    """Schema for updating user profile."""

    preferences: Optional[dict] = None
