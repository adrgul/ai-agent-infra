"""
Configuration management for SupportAI.

Loads environment variables and provides typed configuration.
"""

import os
from typing import Optional
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # OpenAI Configuration
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_model: str = Field("gpt-4-turbo-preview", env="OPENAI_MODEL")

    # Vector Database Configuration
    vector_db_provider: str = Field("pinecone", env="VECTOR_DB_PROVIDER")

    # Pinecone
    pinecone_api_key: Optional[str] = Field(None, env="PINECONE_API_KEY")
    pinecone_environment: Optional[str] = Field(None, env="PINECONE_ENVIRONMENT")
    pinecone_index_name: str = Field("supportai-kb", env="PINECONE_INDEX_NAME")

    # Weaviate
    weaviate_url: Optional[str] = Field(None, env="WEAVIATE_URL")
    weaviate_api_key: Optional[str] = Field(None, env="WEAVIATE_API_KEY")

    # Qdrant
    qdrant_url: Optional[str] = Field(None, env="QDRANT_URL")
    qdrant_api_key: Optional[str] = Field(None, env="QDRANT_API_KEY")

    # Re-ranking
    cohere_api_key: Optional[str] = Field(None, env="COHERE_API_KEY")

    # Logging
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_file: Optional[str] = Field("logs/supportai.log", env="LOG_FILE")

    # Optional Integrations
    zendesk_email: Optional[str] = Field(None, env="ZENDESK_EMAIL")
    zendesk_token: Optional[str] = Field(None, env="ZENDESK_TOKEN")
    zendesk_subdomain: Optional[str] = Field(None, env="ZENDESK_SUBDOMAIN")

    slack_webhook_url: Optional[str] = Field(None, env="SLACK_WEBHOOK_URL")

    smtp_server: Optional[str] = Field(None, env="SMTP_SERVER")
    smtp_port: Optional[int] = Field(None, env="SMTP_PORT")
    smtp_username: Optional[str] = Field(None, env="SMTP_USERNAME")
    smtp_password: Optional[str] = Field(None, env="SMTP_PASSWORD")

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()