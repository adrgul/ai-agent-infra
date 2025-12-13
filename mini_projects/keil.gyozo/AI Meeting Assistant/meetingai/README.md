# MeetingAI - AI Meeting Assistant

AI-Powered Meeting Note Taker + Task Assigner + Summarizer Agent

## Overview

MeetingAI is an intelligent AI agent system that automatically processes meeting notes or transcripts to generate executive summaries, extract action items, and integrate with external tools like Jira, calendars, and email systems.

## Features

- **Executive Summaries**: Generate concise summaries of meeting content
- **Action Item Extraction**: Identify tasks, assignees, and deadlines
- **Multiple Input Formats**: Support for TXT, MD, DOCX, SRT files
- **Structured Output**: JSON format for programmatic access
- **External Integrations**: Jira, Google Calendar, Outlook, Slack, Email
- **LangGraph Workflow**: Robust processing pipeline with error handling

## Installation

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy configuration:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

## Configuration

Edit `config.yaml` and `.env` for your settings:

- LLM API keys (OpenAI, Anthropic)
- Jira credentials
- Email settings
- Calendar integrations

## Usage

### Basic Usage

```python
from meetingai import MeetingProcessor
from meetingai.utils.config import Config

# Load configuration
config = Config.from_yaml("config.yaml")

# Initialize processor
processor = MeetingProcessor(config)

# Process meeting
result = await processor.process("data/meetings/q4_planning.txt")

# Access results
print(result.summary)
print(result.tasks)
```

### Command Line Interface

```bash
# Process a single meeting
python -m meetingai process meeting.txt

# Process with Jira integration
python -m meetingai process meeting.txt --jira --send-email

# Batch process multiple meetings
python -m meetingai batch data/meetings/*.txt
```

## Project Structure

```
meetingai/
├── src/
│   ├── agents/          # LangChain/LangGraph agents
│   ├── workflows/       # LangGraph workflow definitions
│   ├── parsers/         # Input format parsers
│   ├── models/          # Pydantic data models
│   ├── integrations/    # External API integrations
│   └── utils/           # Utility functions
├── tests/               # Unit and integration tests
├── data/                # Sample data and outputs
├── scripts/             # Utility scripts
└── docs/                # Documentation
```

## Development

Run tests:
```bash
pytest
```

Format code:
```bash
black src/
```

Lint code:
```bash
flake8 src/
```

## License

MIT License