"""
Configuration management using Pydantic Settings.

Why this module exists:
- Centralized configuration loaded from environment variables
- Type-safe settings with validation
- Single source of truth for all configurable parameters
- Cached singleton pattern avoids repeated environment reads

Design decisions:
- Pydantic Settings for automatic env var loading and validation
- Frozen config prevents accidental mutation after initialization
- Defaults chosen for local development convenience
- LangSmith settings optional (defaults to disabled)
"""

from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Why frozen: Configuration should not change during runtime;
    enforcing immutability prevents subtle bugs from setting drift.

    Why model_config: Pydantic v2 uses model_config dict for settings;
    env_file enables loading from .env file during development.
    """

    # Assert invariant: OPENAI_API_KEY must not be empty when instantiated in production
    # (This is enforced by Pydantic's required field validation)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        frozen=True,  # Immutable after creation
        extra="ignore",  # Ignore unknown env vars
    )

    # OpenAI Configuration
    # Why required: The app cannot function without an API key
    OPENAI_API_KEY: str = Field(
        ...,  # Required field
        description="OpenAI API key for chat completions and embeddings"
    )

    # Why these defaults: gpt-4.1-mini is cost-effective for demos;
    # text-embedding-3-small balances quality and speed for RAG
    OPENAI_CHAT_MODEL: str = Field(
        default="gpt-4.1-mini",
        description="OpenAI model for chat completions"
    )

    OPENAI_EMBED_MODEL: str = Field(
        default="text-embedding-3-small",
        description="OpenAI model for generating embeddings"
    )

    # File System Paths
    # Why relative paths: Allows running from backend/ directory without complex path resolution
    DOCS_PATH: str = Field(
        default="../data",
        description="Directory containing markdown files to index"
    )

    VECTORSTORE_DIR: str = Field(
        default="../.vectorstore/faiss_index",
        description="Directory where FAISS index is persisted"
    )

    # LangSmith Observability
    # Why optional: Tracing is valuable but not required for basic operation
    LANGSMITH_TRACING: bool = Field(
        default=False,
        description="Enable LangSmith tracing for observability"
    )

    LANGSMITH_API_KEY: Optional[str] = Field(
        default=None,
        description="LangSmith API key (required if LANGSMITH_TRACING=true)"
    )

    LANGSMITH_PROJECT: str = Field(
        default="streamlit-fastapi-faiss-demo",
        description="LangSmith project name for organizing traces"
    )


@lru_cache
def get_settings() -> Settings:
    """
    Retrieve cached application settings singleton.

    Why cached: Settings should be loaded once and reused across the application.
    Reading environment variables repeatedly is wasteful and could lead to
    inconsistencies if the environment changes during runtime.

    Why function: Dependency injection pattern; makes testing easier by allowing
    mock settings to be injected via FastAPI's Depends() mechanism.

    Returns:
        Settings: Immutable application settings instance
    """
    return Settings()
