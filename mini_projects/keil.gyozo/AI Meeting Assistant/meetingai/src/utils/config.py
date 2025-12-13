"""
Configuration management using Pydantic settings
"""

import os
from pathlib import Path
from typing import List, Optional

from pydantic import BaseSettings, Field, validator
from pydantic.types import SecretStr


class LLMConfig(BaseSettings):
    """LLM configuration"""

    provider: str = Field("openai", description="LLM provider")
    model: str = Field("gpt-4-turbo-preview", description="Model name")
    api_key: Optional[SecretStr] = Field(None, description="API key")
    temperature: float = Field(0.3, description="Temperature for generation")
    max_tokens: int = Field(2000, description="Maximum tokens")
    timeout: int = Field(30, description="Request timeout in seconds")


class InputConfig(BaseSettings):
    """Input processing configuration"""

    supported_formats: List[str] = Field(["txt", "md", "docx", "srt"], description="Supported file formats")
    max_file_size_mb: int = Field(10, description="Maximum file size in MB")
    default_language: str = Field("en", description="Default language")
    chunk_size: int = Field(1000, description="Text chunk size")
    chunk_overlap: int = Field(200, description="Chunk overlap")


class OutputConfig(BaseSettings):
    """Output configuration"""

    formats: List[str] = Field(["json", "markdown"], description="Output formats")
    save_path: str = Field("./data/outputs/", description="Output save path")
    timestamp_format: str = Field("%Y%m%d_%H%M%S", description="Timestamp format")
    pretty_json: bool = Field(True, description="Pretty print JSON")


class JiraConfig(BaseSettings):
    """Jira integration configuration"""

    enabled: bool = Field(False, description="Enable Jira integration")
    url: str = Field("", description="Jira instance URL")
    api_token: Optional[SecretStr] = Field(None, description="Jira API token")
    user_email: str = Field("", description="Jira user email")
    project_key: str = Field("MEET", description="Jira project key")
    issue_type: str = Field("Task", description="Issue type")
    default_priority: str = Field("Medium", description="Default priority")


class CalendarConfig(BaseSettings):
    """Calendar integration configuration"""

    enabled: bool = Field(False, description="Enable calendar integration")
    provider: str = Field("google", description="Calendar provider")
    credentials_path: str = Field("./credentials.json", description="Credentials file path")
    default_duration_minutes: int = Field(30, description="Default event duration")
    default_reminder_minutes: int = Field(15, description="Default reminder time")


class EmailConfig(BaseSettings):
    """Email integration configuration"""

    enabled: bool = Field(False, description="Enable email integration")
    provider: str = Field("smtp", description="Email provider")
    smtp_server: str = Field("smtp.gmail.com", description="SMTP server")
    smtp_port: int = Field(587, description="SMTP port")
    use_tls: bool = Field(True, description="Use TLS")
    sender_email: Optional[str] = Field(None, description="Sender email")
    sender_password: Optional[SecretStr] = Field(None, description="Sender password")
    sender_name: str = Field("MeetingAI Bot", description="Sender name")


class SlackConfig(BaseSettings):
    """Slack integration configuration"""

    enabled: bool = Field(False, description="Enable Slack integration")
    webhook_url: Optional[SecretStr] = Field(None, description="Slack webhook URL")
    default_channel: str = Field("#meetings", description="Default channel")
    mention_assignees: bool = Field(True, description="Mention assignees")


class IntegrationsConfig(BaseSettings):
    """All integrations configuration"""

    jira: JiraConfig = Field(default_factory=JiraConfig)
    calendar: CalendarConfig = Field(default_factory=CalendarConfig)
    email: EmailConfig = Field(default_factory=EmailConfig)
    slack: SlackConfig = Field(default_factory=SlackConfig)


class LoggingConfig(BaseSettings):
    """Logging configuration"""

    level: str = Field("INFO", description="Log level")
    file: str = Field("./logs/meetingai.log", description="Log file path")
    format: str = Field("%(asctime)s - %(name)s - %(levelname)s - %(message)s", description="Log format")
    max_bytes: int = Field(10485760, description="Max log file size")
    backup_count: int = Field(5, description="Number of backup files")


class Config(BaseSettings):
    """Main configuration class"""

    llm: LLMConfig = Field(default_factory=LLMConfig)
    llm_fallback: Optional[LLMConfig] = Field(None, description="Fallback LLM config")
    input: InputConfig = Field(default_factory=InputConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    integrations: IntegrationsConfig = Field(default_factory=IntegrationsConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @classmethod
    def from_yaml(cls, path: str) -> "Config":
        """Load configuration from YAML file"""
        import yaml

        config_path = Path(path)
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")

        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        return cls(**data)

    def save_yaml(self, path: str) -> None:
        """Save configuration to YAML file"""
        import yaml

        config_path = Path(path)
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(self.dict(), f, default_flow_style=False)