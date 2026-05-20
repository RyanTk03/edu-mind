"""FastAPI dependencies for authentication and authorization."""

from typing import Annotated

from beanie import PydanticObjectId
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from app.core.exceptions import UnauthorizedError, NotFoundError
from app.core.security import decode_token
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> User:
    """Get the current authenticated user from JWT token."""
    payload = decode_token(token)
    if payload is None:
        raise UnauthorizedError("Invalid or expired token")

    token_type = payload.get("type")
    if token_type != "access":
        raise UnauthorizedError("Invalid token type")

    user_id: str = payload.get("sub")
    if user_id is None:
        raise UnauthorizedError("Invalid token payload")

    try:
        user = await User.get(PydanticObjectId(user_id))
    except Exception:
        raise UnauthorizedError("Invalid user ID")

    if user is None:
        raise NotFoundError("User not found")

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
