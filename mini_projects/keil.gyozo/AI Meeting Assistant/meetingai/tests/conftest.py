"""
Pytest fixtures and configuration
"""

import pytest
from pathlib import Path
from unittest.mock import Mock

from meetingai.utils.config import Config


@pytest.fixture
def sample_config():
    """Sample configuration for testing"""
    config = Mock(spec=Config)

    # Mock LLM config
    config.llm = Mock()
    config.llm.provider = "openai"
    config.llm.model = "gpt-4"
    config.llm.api_key = Mock()
    config.llm.api_key.get_secret_value.return_value = "test-key"

    # Mock input config
    config.input = Mock()
    config.input.supported_formats = ["txt", "md"]

    # Mock output config
    config.output = Mock()
    config.output.save_path = "./data/outputs/"
    config.output.pretty_json = True

    return config


@pytest.fixture
def sample_transcript():
    """Sample meeting transcript for testing"""
    return """
    Meeting: Q4 Sprint Planning
    Date: 2025-12-09
    Attendees: John, Peter, Maria

    John: We need to prioritize the login feature for Q4.
    Peter: I agree. I can handle the backend API setup.
    Maria: I'll work on the UI mockups. Target date December 12.
    John: Good. Let's also review the performance issues.
    Peter: I'll create the API endpoints by December 15.
    """


@pytest.fixture
def sample_meeting_data():
    """Sample meeting data for testing"""
    return {
        "summary": {
            "meeting_id": "MTG-2025-12-09-001",
            "title": "Q4 Sprint Planning",
            "date": "2025-12-09",
            "participants": ["John", "Peter", "Maria"],
            "summary": "Team discussed Q4 priorities including login feature and performance optimization.",
            "key_decisions": ["Login feature is P1", "Performance audit needed"],
            "next_steps": ["UI mockup review", "Backend API setup"]
        },
        "tasks": [
            {
                "task_id": "TASK-001",
                "title": "UI mockup review",
                "assignee": "Maria",
                "due_date": "2025-12-12",
                "priority": "High",
                "status": "to-do"
            },
            {
                "task_id": "TASK-002",
                "title": "Backend API setup",
                "assignee": "Peter",
                "due_date": "2025-12-15",
                "priority": "High",
                "status": "to-do"
            }
        ]
    }


@pytest.fixture
def temp_dir(tmp_path):
    """Temporary directory for testing"""
    return tmp_path


@pytest.fixture
def sample_text_file(temp_dir, sample_transcript):
    """Create a sample text file for testing"""
    file_path = temp_dir / "sample_meeting.txt"
    file_path.write_text(sample_transcript)
    return str(file_path)