# MeetingAI - AI Meeting Assistant Project

## Project Generation Prompt for Visual Studio 2026 AI Assistant

---

## 🎯 Project Overview

**Project Name:** MeetingAI  
**Subtitle:** AI-Powered Meeting Note Taker + Task Assigner + Summarizer Agent  
**Language:** Python 3.11+  
**Framework:** LangChain + LangGraph  

### Core Functionality

Create an intelligent AI agent system that automatically processes meeting notes or transcripts to:

1. ✅ **Generate Executive Summaries** - Extract key points and decisions
2. ✅ **Extract Action Items** - Create to-do lists with task owners and deadlines
3. ✅ **Save Structured Output** - JSON format or direct Jira API integration
4. ✅ **Schedule Calendar Events** - Automatically book follow-up meetings via API
5. ✅ **Send Email Notifications** - Distribute summaries and task assignments to stakeholders

---

## 📊 Business Value & Benefits

| Aspect | Details |
|--------|---------|
| **Simple Start** | Process plain TXT or transcripts without requiring external APIs initially |
| **LangGraph Pattern** | Document input → LLM summarization → JSON output workflow |
| **Extensibility** | Add memory (previous meetings), task tracking, Slack/Teams integration |
| **Business Value** | Time savings, consistent documentation, full audit trail and traceability |

---

## 📋 Required Output Formats

### 1. Meeting Summary JSON

```json
{
  "meeting_id": "MTG-2025-12-09-001",
  "title": "Q4 Sprint Planning",
  "date": "2025-12-09",
  "participants": ["János", "Péter", "Maria"],
  "summary": "A csapat megvitatta a Q4 sprintek prioritásait. Megállapodtak a login feature véglegesítésében és a teljesítmény-optimalizálásban.",
  "key_decisions": [
    "Login feature lesz a P1 prioritás",
    "Performance audit Q4 végéig"
  ],
  "next_steps": [
    "UI mockup review - János - Dec 12",
    "Backend API setup - Péter - Dec 15"
  ]
}
```

### 2. Task List JSON

```json
{
  "tasks": [
    {
      "task_id": "TASK-001",
      "title": "UI mockup review készítése",
      "assignee": "János",
      "due_date": "2025-12-12",
      "priority": "P1",
      "status": "to-do",
      "meeting_reference": "MTG-2025-12-09-001"
    },
    {
      "task_id": "TASK-002",
      "title": "Backend API setup - login endpoint",
      "assignee": "Péter",
      "due_date": "2025-12-15",
      "priority": "P1",
      "status": "to-do",
      "meeting_reference": "MTG-2025-12-09-001"
    }
  ]
}
```

### 3. Jira Integration (Optional)

- Automatic ticket creation via Jira REST API
- Set assignee automatically
- Sync priority levels and due dates
- Link tasks back to meeting reference

---

## 🔄 LangGraph Workflow Architecture

```
┌─────────────────────────┐
│   Document Input        │  ← Input: TXT/Transcript/DOCX/SRT
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│   Parse & Split         │  ← Text chunking & preprocessing
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│   Summarize Node        │  ← LLM generates executive summary
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│   Extract Actions       │  ← LLM extracts action items & owners
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│   Structure JSON        │  ← Validate with Pydantic schemas
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│   Save Output           │  ← Output: JSON file / Jira API / Database
└─────────────────────────┘
```

**Implement this as a LangGraph StateGraph with proper node transitions, error handling, and conditional routing.**

---

## 🛠 Technical Stack Requirements

### Core Technologies

```python
# Backend Framework
- Python 3.11+
- LangChain >= 0.1.0
- LangGraph >= 0.0.20

# LLM Integration
- OpenAI GPT-4 (primary)
- Anthropic Claude (alternative)

# Data Validation & Schemas
- Pydantic >= 2.0.0

# Optional Integrations
- Jira Python SDK >= 3.5.0
- Google Calendar API
- Microsoft Graph API (for Outlook)
- SMTP/SendGrid for emails
```

### Supported Input Formats

- **Plain Text** (.txt) - Simple meeting notes
- **Markdown** (.md) - Structured meeting documentation
- **Subtitle Files** (.srt) - Transcript from video conferencing
- **Word Documents** (.docx) - Formal meeting minutes

### Output Formats

- **JSON** - Structured data for programmatic access
- **Markdown Report** - Human-readable summary document
- **Jira Tickets** - Direct API integration
- **Slack/Teams Messages** - Webhook notifications

---

## 📁 Project Structure

Generate the following complete project structure:

```
meetingai/
│
├── README.md                      # Comprehensive documentation
├── requirements.txt               # Python dependencies
├── setup.py                       # Package installation
├── config.yaml                    # Application configuration
├── .env.example                   # Environment variables template
├── .gitignore                     # Git ignore rules
│
├── src/
│   ├── __init__.py
│   │
│   ├── agents/                    # LangChain/LangGraph agents
│   │   ├── __init__.py
│   │   ├── summarizer.py          # Summary generation agent
│   │   ├── task_extractor.py     # Action item extraction agent
│   │   └── coordinator.py         # Main workflow orchestrator
│   │
│   ├── workflows/                 # LangGraph workflow definitions
│   │   ├── __init__.py
│   │   ├── meeting_processor.py   # Main StateGraph workflow
│   │   └── nodes.py               # Individual workflow nodes
│   │
│   ├── parsers/                   # Input format parsers
│   │   ├── __init__.py
│   │   ├── text_parser.py         # Plain text processor
│   │   ├── markdown_parser.py     # Markdown processor
│   │   ├── docx_parser.py         # Word document processor
│   │   └── srt_parser.py          # Subtitle file processor
│   │
│   ├── models/                    # Pydantic data models
│   │   ├── __init__.py
│   │   ├── meeting.py             # Meeting data models
│   │   ├── task.py                # Task data models
│   │   └── schemas.py             # JSON schemas
│   │
│   ├── integrations/              # External API integrations
│   │   ├── __init__.py
│   │   ├── jira_client.py         # Jira API wrapper
│   │   ├── calendar_client.py     # Calendar API (Google/Outlook)
│   │   ├── email_client.py        # Email service (SMTP/SendGrid)
│   │   └── slack_client.py        # Slack webhook integration
│   │
│   ├── utils/                     # Utility functions
│   │   ├── __init__.py
│   │   ├── config.py              # Configuration loader
│   │   ├── logger.py              # Logging setup
│   │   ├── validators.py          # Data validation helpers
│   │   └── date_utils.py          # Date/time utilities
│   │
│   └── main.py                    # Main application entry point
│
├── tests/                         # Unit and integration tests
│   ├── __init__.py
│   ├── conftest.py                # Pytest fixtures
│   ├── test_summarizer.py
│   ├── test_task_extractor.py
│   ├── test_parsers.py
│   ├── test_integrations.py
│   └── test_workflow.py
│
├── data/                          # Data directory
│   ├── sample_meetings/           # Sample input files
│   │   ├── example_transcript.txt
│   │   ├── example_meeting.md
│   │   └── example_notes.docx
│   ├── outputs/                   # Generated outputs
│   └── templates/                 # Email/report templates
│
├── scripts/                       # Utility scripts
│   ├── run_local.py               # Local development runner
│   └── process_batch.py           # Batch processing script
│
└── docs/                          # Additional documentation
    ├── API.md                     # API documentation
    ├── CONFIGURATION.md           # Configuration guide
    └── DEPLOYMENT.md              # Deployment instructions
```

---

## 🔧 Implementation Requirements

### Phase 1: Core Processing Pipeline

**Generate these modules first:**

1. **Document Parsers** (`src/parsers/`)
   - Handle TXT, MD, DOCX, SRT formats
   - Extract text content
   - Preserve structure and metadata
   - Error handling for corrupt files

2. **Pydantic Models** (`src/models/`)
   - `Meeting` model with all fields from JSON example
   - `Task` model with task properties
   - Proper validation rules
   - Type hints for all fields

3. **LLM Integration** (`src/agents/`)
   - `SummarizerAgent`: Generate executive summaries
   - `TaskExtractorAgent`: Extract action items with assignees
   - Proper prompt engineering
   - Error handling for API failures
   - Retry logic with exponential backoff

4. **LangGraph Workflow** (`src/workflows/meeting_processor.py`)
   - Define StateGraph with nodes matching the workflow diagram
   - Implement proper state management
   - Add conditional edges for error handling
   - Include logging at each node

### Phase 2: Output & Storage

5. **JSON Output Generator**
   - Validate with Pydantic schemas
   - Pretty-print JSON
   - Save to file system
   - Include metadata (timestamp, version)

6. **Markdown Report Generator**
   - Convert JSON to formatted Markdown
   - Include all sections: Summary, Decisions, Action Items
   - Add table of contents
   - Professional formatting

### Phase 3: External Integrations

7. **Jira Integration** (`src/integrations/jira_client.py`)
   - Connect to Jira REST API
   - Create tickets from tasks
   - Set assignee, priority, due date
   - Handle authentication (API token)
   - Error handling and retries

8. **Calendar Integration** (`src/integrations/calendar_client.py`)
   - Google Calendar API support
   - Outlook/Microsoft Graph API support
   - Create events with attendees
   - Set reminders
   - OAuth2 authentication flow

9. **Email Integration** (`src/integrations/email_client.py`)
   - SMTP client for basic email
   - SendGrid API for production
   - HTML email templates
   - Attachment support (PDF summary)
   - Batch sending for multiple recipients

### Phase 4: Advanced Features

10. **Memory System** (Optional but recommended)
    - Store previous meeting summaries
    - Track participant history
    - Project context awareness
    - Vector database integration (ChromaDB/Pinecone)

11. **Slack/Teams Integration** (`src/integrations/slack_client.py`)
    - Webhook-based notifications
    - Rich message formatting
    - Interactive buttons
    - Channel selection

---

## ⚙️ Configuration File Structure

**Generate `config.yaml` with this structure:**

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

---

## 📦 Dependencies (requirements.txt)

```txt
# Core Framework
langchain>=0.1.0
langgraph>=0.0.20
langchain-openai>=0.0.5
langchain-anthropic>=0.0.5

# LLM APIs
openai>=1.10.0
anthropic>=0.8.0

# Data Validation
pydantic>=2.5.0
pydantic-settings>=2.1.0

# Document Processing
python-docx>=1.1.0
python-markdown>=3.5.0

# Jira Integration
jira>=3.5.0

# Calendar Integration
google-api-python-client>=2.100.0
google-auth-httplib2>=0.2.0
google-auth-oauthlib>=1.2.0
msal>=1.25.0  # For Microsoft Graph

# Email
sendgrid>=6.11.0
python-dotenv>=1.0.0

# Utilities
pyyaml>=6.0.1
requests>=2.31.0
python-dateutil>=2.8.2

# Logging & Monitoring
colorlog>=6.8.0

# Testing
pytest>=7.4.3
pytest-asyncio>=0.23.0
pytest-cov>=4.1.0
pytest-mock>=3.12.0

# Development
black>=23.12.0
flake8>=7.0.0
mypy>=1.7.0
```

---

## 💻 Code Generation Requirements

### Code Quality Standards

**Generate all code with:**

1. ✅ **Type Hints** - All functions must have complete type annotations
2. ✅ **Docstrings** - Google-style docstrings for all classes and functions
3. ✅ **Error Handling** - Try/except blocks with specific exception types
4. ✅ **Logging** - Use Python logging module throughout
5. ✅ **Async/Await** - Use async patterns for I/O operations (API calls)
6. ✅ **Validation** - Validate all inputs with Pydantic
7. ✅ **Constants** - No magic numbers or strings
8. ✅ **Clean Code** - Follow PEP 8, max line length 88 chars

### Example Code Structure

**Generate `src/agents/summarizer.py` following this pattern:**

```python
"""
Meeting summarizer agent using LangChain and LLM.

This module contains the SummarizerAgent class that generates
executive summaries from meeting transcripts.
"""

import logging
from typing import Dict, Any, Optional

from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from src.utils.config import Config
from src.models.meeting import MeetingSummary

logger = logging.getLogger(__name__)


class SummarizerAgent:
    """Agent responsible for generating meeting summaries."""
    
    def __init__(self, config: Config):
        """
        Initialize the summarizer agent.
        
        Args:
            config: Application configuration object
        """
        self.config = config
        self.llm = self._initialize_llm()
        self.prompt_template = self._create_prompt_template()
        logger.info("SummarizerAgent initialized successfully")
    
    def _initialize_llm(self) -> ChatOpenAI:
        """Initialize the language model."""
        return ChatOpenAI(
            model=self.config.llm.model,
            temperature=self.config.llm.temperature,
            max_tokens=self.config.llm.max_tokens,
            api_key=self.config.llm.api_key
        )
    
    def _create_prompt_template(self) -> ChatPromptTemplate:
        """Create the prompt template for summarization."""
        template = """
        You are an expert meeting summarizer. Given the following meeting transcript,
        create a concise executive summary.
        
        Meeting Transcript:
        {transcript}
        
        Generate a summary that includes:
        1. Main topics discussed
        2. Key decisions made
        3. Next steps identified
        
        Return the summary in a clear, professional format.
        """
        return ChatPromptTemplate.from_template(template)
    
    async def summarize(
        self, 
        transcript: str,
        participants: Optional[list[str]] = None
    ) -> MeetingSummary:
        """
        Generate a summary from a meeting transcript.
        
        Args:
            transcript: The meeting transcript text
            participants: List of meeting participants
            
        Returns:
            MeetingSummary: Structured summary object
            
        Raises:
            ValueError: If transcript is empty
            RuntimeError: If LLM call fails
        """
        if not transcript or not transcript.strip():
            raise ValueError("Transcript cannot be empty")
        
        try:
            logger.info("Starting summarization process")
            
            # Generate summary using LLM
            prompt = self.prompt_template.format(transcript=transcript)
            response = await self.llm.ainvoke(prompt)
            
            # Parse and validate response
            summary = self._parse_response(response.content, participants)
            
            logger.info("Summarization completed successfully")
            return summary
            
        except Exception as e:
            logger.error(f"Summarization failed: {str(e)}")
            raise RuntimeError(f"Failed to generate summary: {str(e)}")
    
    def _parse_response(
        self, 
        response: str, 
        participants: Optional[list[str]]
    ) -> MeetingSummary:
        """Parse LLM response into structured summary."""
        # Implementation here
        pass
```

### LangGraph Workflow Example

**Generate `src/workflows/meeting_processor.py` with proper StateGraph:**

```python
"""
Main LangGraph workflow for meeting processing.

This module implements the complete meeting processing pipeline
as a LangGraph StateGraph.
"""

import logging
from typing import TypedDict, Annotated
from datetime import datetime

from langgraph.graph import StateGraph, END
from langchain.schema import Document

from src.agents.summarizer import SummarizerAgent
from src.agents.task_extractor import TaskExtractorAgent
from src.models.meeting import Meeting
from src.utils.config import Config

logger = logging.getLogger(__name__)


class MeetingState(TypedDict):
    """State object for the meeting processing workflow."""
    
    document: Document
    parsed_text: str
    summary: dict
    tasks: list[dict]
    errors: list[str]
    metadata: dict


class MeetingProcessor:
    """Main workflow orchestrator using LangGraph."""
    
    def __init__(self, config: Config):
        """Initialize the meeting processor."""
        self.config = config
        self.summarizer = SummarizerAgent(config)
        self.task_extractor = TaskExtractorAgent(config)
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(MeetingState)
        
        # Add nodes
        workflow.add_node("parse", self._parse_node)
        workflow.add_node("summarize", self._summarize_node)
        workflow.add_node("extract_tasks", self._extract_tasks_node)
        workflow.add_node("validate", self._validate_node)
        workflow.add_node("save", self._save_node)
        
        # Add edges
        workflow.add_edge("parse", "summarize")
        workflow.add_edge("summarize", "extract_tasks")
        workflow.add_edge("extract_tasks", "validate")
        workflow.add_conditional_edges(
            "validate",
            self._should_save,
            {
                "save": "save",
                "error": END
            }
        )
        workflow.add_edge("save", END)
        
        # Set entry point
        workflow.set_entry_point("parse")
        
        return workflow.compile()
    
    async def _parse_node(self, state: MeetingState) -> MeetingState:
        """Parse the input document."""
        logger.info("Executing parse node")
        # Implementation
        return state
    
    async def _summarize_node(self, state: MeetingState) -> MeetingState:
        """Generate summary from parsed text."""
        logger.info("Executing summarize node")
        summary = await self.summarizer.summarize(state["parsed_text"])
        state["summary"] = summary.dict()
        return state
    
    async def _extract_tasks_node(self, state: MeetingState) -> MeetingState:
        """Extract action items and tasks."""
        logger.info("Executing task extraction node")
        # Implementation
        return state
    
    async def _validate_node(self, state: MeetingState) -> MeetingState:
        """Validate the generated outputs."""
        logger.info("Executing validation node")
        # Implementation
        return state
    
    async def _save_node(self, state: MeetingState) -> MeetingState:
        """Save outputs to file system and external APIs."""
        logger.info("Executing save node")
        # Implementation
        return state
    
    def _should_save(self, state: MeetingState) -> str:
        """Determine if outputs should be saved."""
        if state.get("errors"):
            return "error"
        return "save"
    
    async def process(self, document_path: str) -> Meeting:
        """
        Process a meeting document through the complete workflow.
        
        Args:
            document_path: Path to the meeting document
            
        Returns:
            Meeting: Complete meeting object with summary and tasks
        """
        initial_state: MeetingState = {
            "document": Document(page_content="", metadata={"path": document_path}),
            "parsed_text": "",
            "summary": {},
            "tasks": [],
            "errors": [],
            "metadata": {"processed_at": datetime.now().isoformat()}
        }
        
        final_state = await self.workflow.ainvoke(initial_state)
        return self._state_to_meeting(final_state)
    
    def _state_to_meeting(self, state: MeetingState) -> Meeting:
        """Convert workflow state to Meeting object."""
        # Implementation
        pass
```

---

## 🧪 Testing Requirements

**Generate comprehensive tests:**

1. **Unit Tests** - Test each component in isolation
2. **Integration Tests** - Test API integrations with mocks
3. **Workflow Tests** - Test complete LangGraph execution
4. **Fixture Data** - Sample meeting transcripts and expected outputs

**Example test structure:**

```python
# tests/test_summarizer.py
import pytest
from src.agents.summarizer import SummarizerAgent
from src.utils.config import Config

@pytest.fixture
def summarizer(mock_config):
    return SummarizerAgent(mock_config)

@pytest.fixture
def sample_transcript():
    return """
    Meeting: Q4 Planning
    Date: 2025-12-09
    Attendees: John, Peter, Maria
    
    John: We need to prioritize the login feature for Q4.
    Peter: I agree. I can handle the backend API setup.
    Maria: I'll work on the UI mockups. Target date December 12.
    """

@pytest.mark.asyncio
async def test_summarizer_basic(summarizer, sample_transcript):
    """Test basic summarization functionality."""
    summary = await summarizer.summarize(sample_transcript)
    
    assert summary.title is not None
    assert len(summary.participants) == 3
    assert "login" in summary.summary.lower()

@pytest.mark.asyncio
async def test_summarizer_empty_transcript(summarizer):
    """Test error handling for empty transcript."""
    with pytest.raises(ValueError):
        await summarizer.summarize("")
```

---

## 📖 Documentation Requirements

**Generate comprehensive README.md with:**

1. Project description and features
2. Installation instructions (pip install, virtual environment)
3. Configuration guide (API keys, config.yaml)
4. Usage examples (CLI and Python API)
5. API documentation for each module
6. Troubleshooting section
7. Contributing guidelines
8. License information

**Example usage section:**

```markdown
## Usage

### Basic Usage

Process a meeting transcript:

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
```

---

## 🚀 Deployment Considerations

**Include in the generated project:**

1. **Docker Support** - Dockerfile and docker-compose.yaml
2. **Environment Variables** - .env.example with all required vars
3. **Health Checks** - Endpoint to verify service status
4. **Graceful Shutdown** - Handle SIGTERM properly
5. **Rate Limiting** - Implement for external API calls
6. **Monitoring** - Structured logging for observability

---

## 🎯 Success Criteria

The generated project must be able to:

- ✅ Accept a meeting transcript file as input
- ✅ Generate a structured summary in under 30 seconds
- ✅ Extract action items with 95%+ accuracy (verified with test cases)
- ✅ Create valid JSON output matching the schema
- ✅ Optionally create Jira tickets when enabled
- ✅ Send email notifications when configured
- ✅ Handle errors gracefully with clear error messages
- ✅ Pass all unit tests with 80%+ code coverage
- ✅ Run without errors on first execution after setup
- ✅ Include clear documentation for setup and usage

---

## 🔮 Future Enhancement Roadmap

**Phase 5: Advanced Features (Document for future)**

1. **Web UI Dashboard**
   - React/Vue.js frontend
   - Real-time processing status
   - Meeting history browser
   - Task management interface

2. **Real-time Processing**
   - WebSocket integration
   - Live transcript processing
   - Streaming LLM responses

3. **Multi-language Support**
   - Detect language automatically
   - Translate summaries
   - Multi-lingual task extraction

4. **Analytics Dashboard**
   - Meeting frequency metrics
   - Task completion rates
   - Participant engagement scores
   - Team productivity insights

5. **Advanced AI Features**
   - Sentiment analysis per participant
   - Speaker diarization (who said what)
   - Meeting effectiveness scoring
   - Automated follow-up suggestions

---

## 📝 Final Instructions for AI Assistant

**Please generate the complete Python project following ALL specifications above:**

1. Create every file in the project structure
2. Implement all core functionality with working code (not stubs)
3. Include complete error handling and logging
4. Write comprehensive docstrings and type hints
5. Generate working unit tests for each module
6. Create a detailed README.md with setup instructions
7. Include sample data files for testing
8. Add configuration templates (.env.example, config.yaml)
9. Ensure the code follows Python best practices (PEP 8, Black formatting)
10. Make the project immediately runnable after installing dependencies

**Code Quality Checklist:**
- [ ] All functions have type hints
- [ ] All classes and functions have docstrings
- [ ] Error handling in all API calls
- [ ] Logging at appropriate levels
- [ ] Pydantic models for all data structures
- [ ] Unit tests for core functionality
- [ ] Integration tests with mocks
- [ ] README with complete setup guide
- [ ] Configuration management via YAML + environment variables
- [ ] Async/await for I/O operations

**The generated project should be production-ready and deployable immediately after configuration.**

---

## 📞 Example End-to-End Flow

```python
# Complete usage example to include in documentation

import asyncio
from meetingai import MeetingProcessor
from meetingai.utils.config import Config

async def main():
    # 1. Load configuration
    config = Config.from_yaml("config.yaml")
    
    # 2. Initialize processor
    processor = MeetingProcessor(config)
    
    # 3. Process meeting
    meeting = await processor.process(
        document_path="data/meetings/q4_planning.txt",
        metadata={
            "title": "Q4 Sprint Planning",
            "date": "2025-12-09",
            "participants": ["John", "Peter", "Maria"]
        }
    )
    
    # 4. Access results
    print("Meeting Summary:")
    print(meeting.summary.summary)
    
    print("\nKey Decisions:")
    for decision in meeting.summary.key_decisions:
        print(f"  - {decision}")
    
    print("\nAction Items:")
    for task in meeting.tasks:
        print(f"  - {task.title} ({task.assignee}) - Due: {task.