"""
Configuration module - Environment variable handling with Pydantic Settings.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # OpenAI API
    openai_api_key: str
    openai_model: str = "gpt-4.1-mini"

    # API Endpoints
    ip_api_url: str = "http://ip-api.com/json"
    holidays_api_url: str = "https://date.nager.at/api/v3/PublicHolidays"


@lru_cache
def get_settings() -> Settings:
    """Singleton pattern for settings."""
    return Settings()
