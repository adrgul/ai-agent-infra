"""Application configuration using pydantic-settings."""
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Server
    port: int = Field(default=8000, description="Server port")

    # OpenAI
    openai_api_key: str = Field(..., description="OpenAI API key")
    openai_model: str = Field(default="gpt-4o-mini", description="OpenAI model name")

    # External APIs
    nominatim_base: str = Field(
        default="https://nominatim.openstreetmap.org",
        description="Nominatim base URL",
    )
    openmeteo_base: str = Field(
        default="https://api.open-meteo.com/v1",
        description="Open-Meteo base URL",
    )

    # Logging
    log_level: str = Field(default="INFO", description="Log level")

    # Data persistence
    data_dir: Path = Field(default=Path("/app/data"), description="Data directory")

    # Agent configuration
    use_langgraph: bool = Field(
        default=True, description="Use LangGraph agent (True) or traditional (False)"
    )

    def ensure_data_dir(self) -> None:
        """Ensure data directory exists."""
        self.data_dir.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
