# Configuration Guide

## Overview

MeetingAI uses a YAML configuration file (`config.yaml`) to manage all settings. Environment variables can be used for sensitive information like API keys.

## Configuration File Structure

```yaml
# LLM Configuration
llm:
  provider: "openai"  # Options: "openai", "anthropic"
  model: "gpt-4-turbo-preview"
  api_key: "${OPENAI_API_KEY}"
  temperature: 0.3
  max_tokens: 2000
  timeout: 30

# Alternative LLM (fallback)
llm_fallback:
  provider: "anthropic"
  model: "claude-3-sonnet-20240229"
  api_key: "${ANTHROPIC_API_KEY}"

# Input Processing
input:
  supported_formats: ["txt", "md", "docx", "srt"]
  max_file_size_mb: 10
  default_language: "en"
  chunk_size: 1000
  chunk_overlap: 200

# Output Configuration
output:
  formats: ["json", "markdown"]
  save_path: "./data/outputs/"
  timestamp_format: "%Y%m%d_%H%M%S"
  pretty_json: true

# Jira Integration
integrations:
  jira:
    enabled: false
    url: "https://your-domain.atlassian.net"
    api_token: "${JIRA_API_TOKEN}"
    user_email: "${JIRA_USER_EMAIL}"
    project_key: "MEET"
    issue_type: "Task"
    default_priority: "Medium"

  # Calendar Integration
  calendar:
    enabled: false
    provider: "google"  # Options: "google", "outlook"
    credentials_path: "./credentials.json"
    default_duration_minutes: 30
    default_reminder_minutes: 15

  # Email Integration
  email:
    enabled: false
    provider: "smtp"  # Options: "smtp", "sendgrid"
    smtp_server: "smtp.gmail.com"
    smtp_port: 587
    use_tls: true
    sender_email: "${EMAIL_ADDRESS}"
    sender_password: "${EMAIL_PASSWORD}"
    sender_name: "MeetingAI Bot"

  # Slack Integration
  slack:
    enabled: false
    webhook_url: "${SLACK_WEBHOOK_URL}"
    default_channel: "#meetings"
    mention_assignees: true

# Logging
logging:
  level: "INFO"  # Options: DEBUG, INFO, WARNING, ERROR
  file: "./logs/meetingai.log"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  max_bytes: 10485760  # 10MB
  backup_count: 5
```

## Environment Variables

Create a `.env` file in the project root:

```bash
# LLM API Keys
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Jira Integration
JIRA_API_TOKEN=your_jira_api_token_here
JIRA_USER_EMAIL=your_jira_email@example.com

# Email Integration
EMAIL_ADDRESS=your_email@example.com
EMAIL_PASSWORD=your_email_password_here

# Slack Integration
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
```

## Configuration Sections

### LLM Configuration

#### OpenAI
```yaml
llm:
  provider: "openai"
  model: "gpt-4-turbo-preview"  # or "gpt-3.5-turbo"
  api_key: "${OPENAI_API_KEY}"
  temperature: 0.3
  max_tokens: 2000
  timeout: 30
```

#### Anthropic Claude
```yaml
llm:
  provider: "anthropic"
  model: "claude-3-sonnet-20240229"
  api_key: "${ANTHROPIC_API_KEY}"
  temperature: 0.3
  max_tokens: 2000
  timeout: 30
```

### Input Processing

```yaml
input:
  supported_formats: ["txt", "md", "docx", "srt"]  # File types to accept
  max_file_size_mb: 10                             # Maximum file size
  default_language: "en"                           # Default language for processing
  chunk_size: 1000                                 # Text chunk size for processing
  chunk_overlap: 200                               # Overlap between chunks
```

### Output Configuration

```yaml
output:
  formats: ["json", "markdown"]           # Output formats to generate
  save_path: "./data/outputs/"            # Where to save outputs
  timestamp_format: "%Y%m%d_%H%M%S"      # Timestamp format for files
  pretty_json: true                       # Pretty-print JSON output
```

### Integration Configuration

#### Jira
```yaml
integrations:
  jira:
    enabled: true
    url: "https://your-domain.atlassian.net"
    api_token: "${JIRA_API_TOKEN}"
    user_email: "${JIRA_USER_EMAIL}"
    project_key: "MEET"
    issue_type: "Task"
    default_priority: "Medium"
```

#### Google Calendar
```yaml
integrations:
  calendar:
    enabled: true
    provider: "google"
    credentials_path: "./credentials.json"
    default_duration_minutes: 30
    default_reminder_minutes: 15
```

#### Outlook Calendar
```yaml
integrations:
  calendar:
    enabled: true
    provider: "outlook"
    # Requires Microsoft Graph API setup
    default_duration_minutes: 30
    default_reminder_minutes: 15
```

#### SMTP Email
```yaml
integrations:
  email:
    enabled: true
    provider: "smtp"
    smtp_server: "smtp.gmail.com"
    smtp_port: 587
    use_tls: true
    sender_email: "${EMAIL_ADDRESS}"
    sender_password: "${EMAIL_PASSWORD}"
    sender_name: "MeetingAI Bot"
```

#### SendGrid Email
```yaml
integrations:
  email:
    enabled: true
    provider: "sendgrid"
    # Requires SendGrid API key
    sender_email: "${EMAIL_ADDRESS}"
    sender_name: "MeetingAI Bot"
```

#### Slack
```yaml
integrations:
  slack:
    enabled: true
    webhook_url: "${SLACK_WEBHOOK_URL}"
    default_channel: "#meetings"
    mention_assignees: true
```

### Logging Configuration

```yaml
logging:
  level: "INFO"                    # DEBUG, INFO, WARNING, ERROR
  file: "./logs/meetingai.log"     # Log file path
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  max_bytes: 10485760              # 10MB - Max log file size
  backup_count: 5                  # Number of backup files
```

## Validation

The configuration is validated using Pydantic models. Invalid configurations will raise validation errors at startup.

## Environment-Specific Configuration

You can create different configuration files for different environments:

- `config.dev.yaml` - Development settings
- `config.prod.yaml` - Production settings
- `config.test.yaml` - Test settings

Load them by passing the path to the Config constructor:

```python
config = Config.from_yaml("config.prod.yaml")
```

## Security Notes

- Never commit API keys or sensitive credentials to version control
- Use environment variables for all secrets
- Regularly rotate API keys
- Use least-privilege access for integrations