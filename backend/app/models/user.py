from datetime import datetime
from enum import Enum
from typing import Optional

from beanie import Document, Indexed, Link
from pydantic import EmailStr, Field


class LearnerLevel(str, Enum):
    """Learner proficiency level."""

    DEBUTANT = "débutant"
    INTERMEDIAIRE = "intermédiaire"
    AVANCE = "avancé"


class User(Document):
    """User document - authentication and basic info."""

    email: Indexed(EmailStr, unique=True)
    password_hash: str
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "users"


class UserProfile(Document):
    """User learning profile - tracks progress and preferences."""

    user: Link[User]
    level: LearnerLevel = LearnerLevel.DEBUTANT
    level_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)  # None = not assessed
    exercises_completed: int = Field(default=0)
    weak_points: list[str] = Field(default_factory=list)
    strong_points: list[str] = Field(default_factory=list)
    preferences: dict = Field(default_factory=dict)

    class Settings:
        name = "user_profiles"
