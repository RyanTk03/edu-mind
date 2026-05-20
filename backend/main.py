"""
EDU-MIND Backend Application Entry Point.

Usage (from backend/ directory):
    .venv/bin/python main.py                    # Verify database connection
    .venv/bin/python -m app.seeds.seed          # Seed test data
    .venv/bin/python -m app.seeds.seed --clear  # Clear all data

Or with uv (if no other venv is active):
    uv run python main.py
    uv run python -m app.seeds.seed
"""

import asyncio

from app.core.database import init_db


async def main() -> None:
    """Initialize and verify database connection."""
    print("Connecting to database...")
    await init_db()
    print("Database connection successful.")


if __name__ == "__main__":
    asyncio.run(main())
