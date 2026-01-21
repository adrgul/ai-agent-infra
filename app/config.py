"""
Configuration module for the agent demo application.
Loads settings from environment variables with sensible defaults.
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # OpenAI (optional)
    openai_api_key: Optional[str] = None
    
    # Model Names
    model_cheap: str = "gpt-3.5-turbo"
    model_medium: str = "gpt-4-turbo-preview"
    model_expensive: str = "gpt-4"
    
    # Pricing (USD per 1K tokens)
    price_cheap_input: float = 0.0001
    price_cheap_output: float = 0.0002
    price_medium_input: float = 0.001
    price_medium_output: float = 0.002
    price_expensive_input: float = 0.01
    price_expensive_output: float = 0.03
    
    # Cache
    cache_ttl_seconds: int = 3600
    cache_max_size: int = 1000
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
