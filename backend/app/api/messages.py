"""Chat/message endpoints."""

from beanie import PydanticObjectId
from fastapi import APIRouter

from app.api import get_link_id, check_link_id
from app.core.deps import CurrentUser
from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.message import Message, MessageRole
from app.models.session import Session
from app.models.user import UserProfile
from app.schemas.message import ChatHistoryResponse, MessageCreate, MessageResponse
from app.services.ai_service import AIService

router = APIRouter(prefix="/sessions/{session_id}/chat", tags=["Chat"])


async def verify_session_ownership(
    session_id: str, current_user: CurrentUser
) -> Session:
    """Verify session exists and belongs to current user."""
    try:
        session = await Session.get(PydanticObjectId(session_id))
    except Exception:
        raise NotFoundError("Session not found")

    if not session:
        raise NotFoundError("Session not found")

    if not check_link_id(session.user, current_user.id):
        raise ForbiddenError("Not your session")

    return session


def message_to_response(message: Message) -> MessageResponse:
    """Convert message model to response schema."""
    return MessageResponse(
        id=str(message.id),
        session_id=get_link_id(message.session),
        role=message.role,
        content=message.content,
        created_at=message.created_at,
        metadata=message.metadata,
    )


@router.get("/", response_model=ChatHistoryResponse)
async def get_chat_history(session_id: str, current_user: CurrentUser):
    """Get chat history for a session."""
    session = await verify_session_ownership(session_id, current_user)

    messages = await Message.find(Message.session.id == session.id).sort(
        "+created_at"
    ).to_list()

    return ChatHistoryResponse(
        messages=[message_to_response(m) for m in messages],
        total=len(messages),
    )


@router.post("/", response_model=MessageResponse)
async def send_message(
    session_id: str, data: MessageCreate, current_user: CurrentUser
):
    """Send a message and get AI response."""
    session = await verify_session_ownership(session_id, current_user)

    # Save user message
    user_message = Message(
        session=session,
        role=MessageRole.USER,
        content=data.content,
    )
    await user_message.insert()

    # Get user profile for student level
    profile = await UserProfile.find_one(UserProfile.user.id == current_user.id)
    student_level = profile.level_score if profile else 0.5

    # Get session metadata for current exercise state
    session_metadata = session.metadata or {}
    current_exercise = session_metadata.get("current_exercise")
    history = session_metadata.get("exercise_history", [])

    # Process message through AI workflow
    result = await AIService.process_message(
        session_id=session_id,
        message=data.content,
        student_level=student_level,
        history=history,
        current_exercise=current_exercise,
    )

    # Save AI response
    ai_message = Message(
        session=session,
        role=MessageRole.AI,
        content=result["response"],
        metadata={
            "intent": result.get("intent"),
            "has_exercise": result.get("current_exercise") is not None,
        },
    )
    await ai_message.insert()

    # Update session metadata with exercise state
    if result.get("current_exercise"):
        session.metadata = session.metadata or {}
        session.metadata["current_exercise"] = result["current_exercise"]
        await session.save()

    # Clear exercise after correction
    if result.get("correction"):
        session.metadata = session.metadata or {}
        # Add to history
        history = session.metadata.get("exercise_history", [])
        history.append({
            "exercise": current_exercise,
            "correction": result["correction"],
        })
        session.metadata["exercise_history"] = history[-10:]  # Keep last 10
        session.metadata["current_exercise"] = None
        await session.save()

        # Update user profile level
        if profile and result.get("updated_level"):
            profile.level_score = result["updated_level"]
            # Update weak/strong points from correction
            correction = result["correction"]
            if correction.get("errors"):
                for error in correction["errors"]:
                    if error not in profile.weak_points:
                        profile.weak_points.append(error)
            await profile.save()

    return message_to_response(ai_message)


@router.delete("/")
async def clear_chat_history(session_id: str, current_user: CurrentUser):
    """Clear all messages in a session's chat."""
    session = await verify_session_ownership(session_id, current_user)

    result = await Message.find(Message.session.id == session.id).delete()

    return {"message": f"Deleted {result.deleted_count} messages"}
