from __future__ import annotations

import os
from dataclasses import dataclass

#from dotenv import load_dotenv

try:
    from dotenv import load_dotenv  # type: ignore
except ImportError:
    def load_dotenv(*args, **kwargs):
        raise RuntimeError(
            "python-dotenv is not installed. Install it with: pip install python-dotenv"
        )

load_dotenv()


@dataclass(frozen=True)
class Config:
    """Simple configuration holder.

    Reads configuration from environment variables. Keeps configuration outside
    of business logic (Dependency Inversion).
    """

    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    embedding_model: str = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    chroma_dir: str = os.getenv("CHROMA_DIR", "./chroma_db")
    chroma_collection: str = os.getenv("CHROMA_COLLECTION", "prompts")


def load_config() -> Config:
    cfg = Config()
    if not cfg.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY not set. Copy .env.example to .env and set it.")
    return cfg
