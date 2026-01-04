"""Configuration loader.

Loads settings from a .env file using python-dotenv and exposes
typed configuration values.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class Config:
    openai_api_key: str
    embedding_model: str
    chroma_persist_dir: str


def load_config(env_path: str | None = None) -> Config:
    """Load configuration from `.env` or environment.

    Args:
        env_path: Optional path to .env file. If None, dotenv searches for `.env`.
    """
    if env_path:
        load_dotenv(env_path)
    else:
        load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set. Copy .env.example -> .env and set the key.")

    model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    chroma_dir = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")

    return Config(openai_api_key=api_key, embedding_model=model, chroma_persist_dir=chroma_dir)
