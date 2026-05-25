"""
AI Configuration for EDU-MIND.

Centralizes all AI-related settings.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings


class AISettings(BaseSettings):
    """AI-specific settings."""

    # LLM Configuration (GROQ_API_KEY without prefix)
    groq_api_key: str = ""
    model_name: str = "llama-3.3-70b-versatile"
    router_model: str = "llama-3.1-8b-instant"
    temperature: float = 0.7
    max_tokens: int = 1000

    # Student Level Configuration
    alpha_correct: float = 0.25  # Learning rate for correct answers
    alpha_incorrect: float = 0.10  # Learning rate for incorrect answers
    level_min: float = 0.05
    level_max: float = 0.95

    # RAG Configuration
    chroma_persist_dir: str = ""
    embedding_model: str = "all-MiniLM-L6-v2"
    chunk_size: int = 500
    chunk_overlap: int = 50
    default_k: int = 5  # Number of chunks to retrieve

    class Config:
        env_file = ".env"
        extra = "ignore"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Set default chroma directory if not specified
        if not self.chroma_persist_dir:
            object.__setattr__(
                self,
                "chroma_persist_dir",
                str(Path(__file__).parent.parent.parent.parent / "data" / "chroma_db"),
            )


# Singleton instance
ai_settings = AISettings()
