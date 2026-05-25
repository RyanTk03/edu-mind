"""Chat/message endpoints."""

from beanie import PydanticObjectId
from fastapi import APIRouter

from app.core.deps import CurrentUser
from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.message import Message, MessageRole
from app.models.session import Session
from app.schemas.message import ChatHistoryResponse, MessageCreate, MessageResponse

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

    if session.user.ref.id != current_user.id:
        raise ForbiddenError("Not your session")

    return session


def message_to_response(message: Message) -> MessageResponse:
    """Convert message model to response schema."""
    return MessageResponse(
        id=str(message.id),
        session_id=str(message.session.ref.id),
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
    """Send a message (user message only for now, AI response requires agent integration)."""
    session = await verify_session_ownership(session_id, current_user)

    # Save user message
    user_message = Message(
        session=session,
        role=MessageRole.USER,
        content=data.content,
    )
    await user_message.insert()

    # TODO: AI agent integration
    # For now, we just save the user message.
    # Later, the feedback agent will:
    # 1. Query ChromaDB for relevant context
    # 2. Generate AI response
    # 3. Save AI message and return both

    return message_to_response(user_message)


@router.delete("/")
async def clear_chat_history(session_id: str, current_user: CurrentUser):
    """Clear all messages in a session's chat."""
    session = await verify_session_ownership(session_id, current_user)

    result = await Message.find(Message.session.id == session.id).delete()

    return {"message": f"Deleted {result.deleted_count} messages"}
