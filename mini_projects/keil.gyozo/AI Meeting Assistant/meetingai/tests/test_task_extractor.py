"""
Tests for the task extractor agent
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from meetingai.agents.task_extractor import TaskExtractorAgent
from meetingai.models.task import TaskList


@pytest.fixture
def task_extractor(sample_config):
    return TaskExtractorAgent(sample_config)


@pytest.mark.asyncio
async def test_task_extractor_initialization(task_extractor, sample_config):
    """Test task extractor agent initialization"""
    assert task_extractor.config == sample_config
    assert task_extractor.llm is not None
    assert task_extractor.prompt_template is not None


@pytest.mark.asyncio
async def test_extract_tasks_basic(task_extractor, sample_transcript):
    """Test basic task extraction functionality"""
    with patch.object(task_extractor.llm, 'ainvoke', new_callable=AsyncMock) as mock_invoke:
        # Mock LLM response
        mock_response = Mock()
        mock_response.content = '''{
            "tasks": [
                {
                    "title": "UI mockup review",
                    "assignee": "Maria",
                    "due_date": "2025-12-12",
                    "priority": "High"
                },
                {
                    "title": "Backend API setup",
                    "assignee": "Peter",
                    "due_date": "2025-12-15",
                    "priority": "High"
                }
            ]
        }'''
        mock_invoke.return_value = mock_response

        # Call extract_tasks
        result = await task_extractor.extract_tasks(sample_transcript, ["John", "Peter", "Maria"])

        # Verify result
        assert isinstance(result, TaskList)
        assert len(result.tasks) == 2

        task1 = result.tasks[0]
        assert task1.title == "UI mockup review"
        assert task1.assignee == "Maria"
        assert task1.due_date == "2025-12-12"
        assert task1.priority == "High"

        task2 = result.tasks[1]
        assert task2.title == "Backend API setup"
        assert task2.assignee == "Peter"


@pytest.mark.asyncio
async def test_extract_tasks_empty_transcript(task_extractor):
    """Test error handling for empty transcript"""
    with pytest.raises(ValueError, match="Transcript cannot be empty"):
        await task_extractor.extract_tasks("", [])


@pytest.mark.asyncio
async def test_extract_tasks_no_tasks_found(task_extractor, sample_transcript):
    """Test handling when no tasks are found"""
    with patch.object(task_extractor.llm, 'ainvoke', new_callable=AsyncMock) as mock_invoke:
        mock_response = Mock()
        mock_response.content = '{"tasks": []}'
        mock_invoke.return_value = mock_response

        result = await task_extractor.extract_tasks(sample_transcript, [])

        assert isinstance(result, TaskList)
        assert len(result.tasks) == 0


@pytest.mark.asyncio
async def test_extract_tasks_invalid_json(task_extractor, sample_transcript):
    """Test handling of invalid JSON response"""
    with patch.object(task_extractor.llm, 'ainvoke', new_callable=AsyncMock) as mock_invoke:
        mock_response = Mock()
        mock_response.content = "Invalid JSON response"
        mock_invoke.return_value = mock_response

        result = await task_extractor.extract_tasks(sample_transcript, [])

        # Should return empty task list on JSON error
        assert isinstance(result, TaskList)
        assert len(result.tasks) == 0


@pytest.mark.asyncio
async def test_extract_tasks_with_meeting_id(task_extractor, sample_transcript):
    """Test task extraction with meeting ID reference"""
    meeting_id = "MTG-2025-12-09-001"

    with patch.object(task_extractor.llm, 'ainvoke', new_callable=AsyncMock) as mock_invoke:
        mock_response = Mock()
        mock_response.content = '''{
            "tasks": [
                {
                    "title": "Test task",
                    "assignee": "John",
                    "priority": "Medium"
                }
            ]
        }'''
        mock_invoke.return_value = mock_response

        result = await task_extractor.extract_tasks(sample_transcript, [], meeting_id)

        assert len(result.tasks) == 1
        assert result.tasks[0].meeting_reference == meeting_id