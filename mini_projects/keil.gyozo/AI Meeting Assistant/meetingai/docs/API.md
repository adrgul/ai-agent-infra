# MeetingAI API Documentation

## Overview

MeetingAI provides both a Python API and a command-line interface for processing meeting transcripts and generating structured outputs.

## Python API

### MeetingProcessor

The main class for processing meetings.

```python
from meetingai import MeetingProcessor
from meetingai.utils.config import Config

# Load configuration
config = Config.from_yaml("config.yaml")

# Initialize processor
processor = MeetingProcessor(config)

# Process a meeting
result = await processor.process("meeting.txt")
```

#### Methods

##### `process(document_path, participants=None, metadata=None)`

Process a meeting document.

**Parameters:**
- `document_path` (str): Path to the meeting document
- `participants` (list, optional): List of participant names
- `metadata` (dict, optional): Additional metadata

**Returns:** `Meeting` object

**Raises:** `RuntimeError` if processing fails

### Meeting Object

Represents a processed meeting with summary and tasks.

#### Attributes

- `summary` (MeetingSummary): Meeting summary information
- `tasks` (list): List of Task objects
- `metadata` (dict): Additional metadata
- `processed_at` (datetime): Processing timestamp

### MeetingSummary Object

Contains the meeting summary information.

#### Attributes

- `meeting_id` (str): Unique meeting identifier
- `title` (str): Meeting title
- `date` (str): Meeting date (YYYY-MM-DD)
- `participants` (list): List of participants
- `summary` (str): Executive summary
- `key_decisions` (list): Key decisions made
- `next_steps` (list): Next steps identified

### Task Object

Represents an action item or task.

#### Attributes

- `task_id` (str): Unique task identifier
- `title` (str): Task title
- `assignee` (str): Person assigned to the task
- `due_date` (str, optional): Due date (YYYY-MM-DD)
- `priority` (str): Task priority (Low, Medium, High, P1, P2, P3)
- `status` (str): Task status (to-do, in-progress, done, cancelled)
- `meeting_reference` (str): Reference to originating meeting

## Command Line Interface

### Basic Usage

```bash
# Process a single meeting
python -m meetingai process meeting.txt

# Process with Jira integration
python -m meetingai process meeting.txt --jira

# Process multiple meetings
python -m meetingai batch meeting1.txt meeting2.txt
```

### Options

#### process command

- `--config, -c`: Path to configuration file (default: config.yaml)
- `--jira`: Enable Jira integration
- `--email`: Send email notifications
- `--calendar`: Create calendar events
- `--slack`: Send Slack notifications

#### batch command

- `--config, -c`: Path to configuration file
- `--output-dir, -o`: Output directory (default: ./data/outputs)

## Configuration

MeetingAI uses a YAML configuration file. See `config.yaml` for all available options.

### LLM Configuration

```yaml
llm:
  provider: "openai"  # or "anthropic"
  model: "gpt-4-turbo-preview"
  api_key: "${OPENAI_API_KEY}"
  temperature: 0.3
  max_tokens: 2000
```

### Integration Configuration

```yaml
integrations:
  jira:
    enabled: true
    url: "https://your-domain.atlassian.net"
    api_token: "${JIRA_API_TOKEN}"
    project_key: "MEET"

  email:
    enabled: true
    provider: "smtp"
    smtp_server: "smtp.gmail.com"
    sender_email: "${EMAIL_ADDRESS}"
```

## Supported File Formats

- **Plain Text** (.txt): Simple meeting notes
- **Markdown** (.md): Structured meeting documentation
- **Word Documents** (.docx): Formal meeting minutes
- **SRT Subtitles** (.srt): Transcripts from video recordings

## Error Handling

The API provides comprehensive error handling:

- `ValueError`: Invalid input parameters
- `FileNotFoundError`: Input file not found
- `RuntimeError`: Processing failures
- `ConnectionError`: Integration API failures

## Examples

### Complete Processing Example

```python
import asyncio
from meetingai import MeetingProcessor
from meetingai.utils.config import Config

async def process_meeting():
    # Load config
    config = Config.from_yaml("config.yaml")

    # Initialize
    processor = MeetingProcessor(config)

    # Process
    meeting = await processor.process(
        document_path="data/meetings/q4_planning.txt",
        participants=["John", "Peter", "Maria"],
        metadata={"priority": "high"}
    )

    # Access results
    print(f"Meeting: {meeting.summary.title}")
    print(f"Summary: {meeting.summary.summary}")

    for task in meeting.tasks:
        print(f"Task: {task.title} -> {task.assignee}")

asyncio.run(process_meeting())
```

### Custom Configuration

```python
from meetingai.utils.config import Config

# Load from file
config = Config.from_yaml("config.yaml")

# Or create programmatically
config = Config(
    llm={
        "provider": "openai",
        "model": "gpt-4",
        "api_key": "your-key"
    },
    output={
        "save_path": "./outputs/",
        "pretty_json": True
    }
)
```