from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration driven by environment variables."""

    openai_api_key: str = Field(default="", env="OPENAI_API_KEY")
    data_dir: Path = Field(default=Path("data"), env="DATA_DIR")
    model_name: str = Field(default="gpt-4o-mini", env="OPENAI_MODEL")
    # Web search integration removed — search-related env vars are no longer used.

    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "protected_namespaces": ("settings_",),
    }


settings = Settings()

# Ensure base data folders exist early to simplify downstream logic
settings.data_dir.mkdir(parents=True, exist_ok=True)
settings.data_dir.joinpath("conversations").mkdir(parents=True, exist_ok=True)
settings.data_dir.joinpath("users").mkdir(parents=True, exist_ok=True)
