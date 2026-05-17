from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings
from app.models.user import User, UserProfile
from app.models.session import Session
from app.models.attachment import Attachment
from app.models.message import Message
from app.models.exercise import Exercise


async def init_db():
    """Initialize MongoDB connection and Beanie ODM."""
    client = AsyncIOMotorClient(settings.mongodb_url)

    await init_beanie(
        database=client[settings.database_name],
        document_models=[
            User,
            UserProfile,
            Session,
            Attachment,
            Message,
            Exercise,
        ],
    )


async def close_db(client: AsyncIOMotorClient):
    """Close MongoDB connection."""
    client.close()
