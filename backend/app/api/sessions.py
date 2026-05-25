"""Session CRUD endpoints."""

from datetime import datetime, timezone

from beanie import PydanticObjectId
from fastapi import APIRouter

from app.api import get_link_id, check_link_id
from app.core.deps import CurrentUser
from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.attachment import Attachment
from app.models.exercise import Exercise
from app.models.message import Message
from app.models.session import Session
from app.schemas.session import (
    SessionCreate,
    SessionListResponse,
    SessionResponse,
    SessionUpdate,
)

router = APIRouter(prefix="/sessions", tags=["Sessions"])


async def get_session_counts(session_id: PydanticObjectId) -> tuple[int, int, int]:
    """Get counts of attachments, messages, and exercises for a session."""
    attachment_count = await Attachment.find(
        Attachment.session.id == session_id
    ).count()
    message_count = await Message.find(Message.session.id == session_id).count()
    exercise_count = await Exercise.find(Exercise.session.id == session_id).count()
    return attachment_count, message_count, exercise_count


def session_to_response(
    session: Session,
    attachment_count: int = 0,
    message_count: int = 0,
    exercise_count: int = 0,
) -> SessionResponse:
    """Convert session model to response schema."""
    return SessionResponse(
        id=str(session.id),
        user_id=get_link_id(session.user),
        title=session.title,
        description=session.description,
        created_at=session.created_at,
        updated_at=session.updated_at,
        attachment_count=attachment_count,
        message_count=message_count,
        exercise_count=exercise_count,
    )


@router.get("/", response_model=SessionListResponse)
async def list_sessions(current_user: CurrentUser):
    """List all sessions for current user."""
    sessions = await Session.find(Session.user.id == current_user.id).to_list()

    session_responses = []
    for session in sessions:
        counts = await get_session_counts(session.id)
        session_responses.append(session_to_response(session, *counts))

    return SessionListResponse(sessions=session_responses, total=len(session_responses))


@router.post("/", response_model=SessionResponse)
async def create_session(data: SessionCreate, current_user: CurrentUser):
    """Create a new study session."""
    session = Session(
        user=current_user,
        title=data.title,
        description=data.description,
    )
    await session.insert()

    return session_to_response(session)


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str, current_user: CurrentUser):
    """Get a specific session."""
    try:
        session = await Session.get(PydanticObjectId(session_id))
    except Exception:
        raise NotFoundError("Session not found")

    if not session:
        raise NotFoundError("Session not found")

    if not check_link_id(session.user, current_user.id):
        raise ForbiddenError("Not your session")

    counts = await get_session_counts(session.id)
    return session_to_response(session, *counts)


@router.patch("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: str, data: SessionUpdate, current_user: CurrentUser
):
    """Update a session."""
    try:
        session = await Session.get(PydanticObjectId(session_id))
    except Exception:
        raise NotFoundError("Session not found")

    if not session:
        raise NotFoundError("Session not found")

    if not check_link_id(session.user, current_user.id):
        raise ForbiddenError("Not your session")

    if data.title is not None:
        session.title = data.title
    if data.description is not None:
        session.description = data.description

    session.updated_at = datetime.now(timezone.utc)
    await session.save()

    counts = await get_session_counts(session.id)
    return session_to_response(session, *counts)


@router.delete("/{session_id}")
async def delete_session(session_id: str, current_user: CurrentUser):
    """Delete a session and all its related data."""
    try:
        session = await Session.get(PydanticObjectId(session_id))
    except Exception:
        raise NotFoundError("Session not found")

    if not session:
        raise NotFoundError("Session not found")

    if not check_link_id(session.user, current_user.id):
        raise ForbiddenError("Not your session")

    # Delete related data
    await Attachment.find(Attachment.session.id == session.id).delete()
    await Message.find(Message.session.id == session.id).delete()
    await Exercise.find(Exercise.session.id == session.id).delete()

    await session.delete()

    return {"message": "Session deleted successfully"}
