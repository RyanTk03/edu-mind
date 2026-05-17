"""
Database seeding script.

Usage (from backend/ directory):
    .venv/bin/python -m app.seeds.seed          # Seed the database
    .venv/bin/python -m app.seeds.seed --clear  # Clear all data
"""

import asyncio
import sys

from app.core.database import init_db
from app.models import User, UserProfile, Session, Attachment, Message, Exercise
from app.models.exercise import ExerciseMode
from app.models.message import MessageRole


async def seed_database() -> None:
    """Seed the database with test data."""
    await init_db()

    # Check if data already exists
    existing_user = await User.find_one(User.email == "test@example.com")
    if existing_user:
        print("Database already seeded. Use --clear to reset.")
        return

    print("Seeding database...\n")

    # 1. Create User
    user = User(
        email="test@example.com",
        password_hash="hashed_password_placeholder",
        name="Test User"
    )
    await user.insert()
    print(f"  [+] User: {user.name} ({user.email})")

    # 2. Create UserProfile
    profile = UserProfile(user=user)
    await profile.insert()
    print(f"  [+] UserProfile: linked to {user.name}")

    # 3. Create Session
    session = Session(
        user=user,
        title="Introduction to Python",
        description="Learning Python basics"
    )
    await session.insert()
    print(f"  [+] Session: {session.title}")

    # 4. Create Attachment
    attachment = Attachment(
        session=session,
        filename="python_guide.pdf",
        original_filename="python_guide.pdf",
        file_type="application/pdf",
        file_size=2048,
        file_path="/uploads/python_guide.pdf"
    )
    await attachment.insert()
    print(f"  [+] Attachment: {attachment.filename}")

    # 5. Create Message
    message = Message(
        session=session,
        role=MessageRole.USER,
        content="Can you explain Python variables?"
    )
    await message.insert()
    print(f"  [+] Message: \"{message.content[:40]}...\"")

    # 6. Create Exercise
    exercise = Exercise(
        session=session,
        title="Python Variables Quiz",
        mode=ExerciseMode.FREE
    )
    await exercise.insert()
    print(f"  [+] Exercise: {exercise.title}")

    print("\nDatabase seeded successfully.")


async def clear_database() -> None:
    """Clear all data from the database."""
    await init_db()

    print("Clearing database...\n")

    # Delete in reverse order of dependencies
    deleted = await Exercise.delete_all()
    print(f"  [-] Exercises: {deleted.deleted_count} deleted")

    deleted = await Message.delete_all()
    print(f"  [-] Messages: {deleted.deleted_count} deleted")

    deleted = await Attachment.delete_all()
    print(f"  [-] Attachments: {deleted.deleted_count} deleted")

    deleted = await Session.delete_all()
    print(f"  [-] Sessions: {deleted.deleted_count} deleted")

    deleted = await UserProfile.delete_all()
    print(f"  [-] UserProfiles: {deleted.deleted_count} deleted")

    deleted = await User.delete_all()
    print(f"  [-] Users: {deleted.deleted_count} deleted")

    print("\nDatabase cleared.")


async def main() -> None:
    """Entry point for seeding script."""
    if "--clear" in sys.argv:
        await clear_database()
    else:
        await seed_database()


if __name__ == "__main__":
    asyncio.run(main())
