"""Authentication endpoints."""

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.core.deps import CurrentUser
from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import (
    create_tokens,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.models.user import User, UserProfile
from app.schemas.user import (
    TokenRefresh,
    TokenResponse,
    UserCreate,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=TokenResponse)
async def register(data: UserCreate):
    """Register a new user account."""
    existing = await User.find_one(User.email == data.email)
    if existing:
        raise ConflictError("Email already registered")

    user = User(
        email=data.email,
        password_hash=get_password_hash(data.password),
        name=data.name,
    )
    await user.insert()

    profile = UserProfile(user=user)
    await profile.insert()

    access_token, refresh_token = create_tokens(str(user.id))
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/login", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login and get JWT tokens."""
    user = await User.find_one(User.email == form_data.username)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise UnauthorizedError("Incorrect email or password")

    access_token, refresh_token = create_tokens(str(user.id))
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(data: TokenRefresh):
    """Refresh access token using refresh token."""
    payload = decode_token(data.refresh_token)
    if payload is None:
        raise UnauthorizedError("Invalid refresh token")

    if payload.get("type") != "refresh":
        raise UnauthorizedError("Invalid token type")

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedError("Invalid token payload")

    user = await User.get(user_id)
    if not user:
        raise UnauthorizedError("User not found")

    access_token, refresh_token = create_tokens(str(user.id))
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser):
    """Get current authenticated user."""
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        name=current_user.name,
        created_at=current_user.created_at,
    )
