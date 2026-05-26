"""User profile endpoints."""

from fastapi import APIRouter

from app.core.deps import CurrentUser
from app.core.exceptions import NotFoundError
from app.models.user import UserProfile
from app.schemas.user import UserProfileResponse, UserProfileUpdate

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/profile", response_model=UserProfileResponse)
async def get_profile(current_user: CurrentUser):
    """Get current user's learning profile."""
    profile = await UserProfile.find_one(UserProfile.user.id == current_user.id)
    if not profile:
        raise NotFoundError("Profile not found")

    return UserProfileResponse(
        id=str(profile.id),
        user_id=str(current_user.id),
        level=profile.level,
        level_score=profile.level_score,
        exercises_completed=profile.exercises_completed or 0,
        weak_points=profile.weak_points,
        strong_points=profile.strong_points,
        preferences=profile.preferences,
    )


@router.patch("/profile", response_model=UserProfileResponse)
async def update_profile(data: UserProfileUpdate, current_user: CurrentUser):
    """Update current user's profile preferences."""
    profile = await UserProfile.find_one(UserProfile.user.id == current_user.id)
    if not profile:
        raise NotFoundError("Profile not found")

    if data.preferences is not None:
        profile.preferences.update(data.preferences)
        await profile.save()

    return UserProfileResponse(
        id=str(profile.id),
        user_id=str(current_user.id),
        level=profile.level,
        level_score=profile.level_score,
        exercises_completed=profile.exercises_completed or 0,
        weak_points=profile.weak_points,
        strong_points=profile.strong_points,
        preferences=profile.preferences,
    )
