"""
Tests for the LangGraph workflow
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from meetingai.workflows.meeting_processor import MeetingProcessor
from meetingai.models.meeting import Meeting


@pytest.fixture
def workflow_processor(sample_config):
    return MeetingProcessor(sample_config)


@pytest.mark.asyncio
async def test_workflow_initialization(workflow_processor, sample_config):
    """Test workflow processor initialization"""
    assert workflow_processor.config == sample_config
    assert workflow_processor.workflow is not None


@pytest.mark.asyncio
async def test_workflow_process_complete(workflow_processor, sample_text_file, sample_config):
    """Test complete workflow processing"""
    # Mock the node classes
    with patch('meetingai.workflows.meeting_processor.ParseNode') as mock_parse, \
         patch('meetingai.workflows.meeting_processor.SummarizeNode') as mock_summarize, \
         patch('meetingai.workflows.meeting_processor.ExtractTasksNode') as mock_extract, \
         patch('meetingai.workflows.meeting_processor.ValidateNode') as mock_validate, \
         patch('meetingai.workflows.meeting_processor.SaveNode') as mock_save:

        # Setup mocks
        mock_parse_instance = AsyncMock()
        mock_parse_instance.__call__ = AsyncMock()
        mock_parse.return_value = mock_parse_instance

        mock_summarize_instance = AsyncMock()
        mock_summarize_instance.__call__ = AsyncMock()
        mock_summarize.return_value = mock_summarize_instance

        mock_extract_instance = AsyncMock()
        mock_extract_instance.__call__ = AsyncMock()
        mock_extract.return_value = mock_extract_instance

        mock_validate_instance = AsyncMock()
        mock_validate_instance.__call__ = AsyncMock()
        mock_validate.return_value = mock_validate_instance

        mock_save_instance = AsyncMock()
        mock_save_instance.__call__ = AsyncMock()
        mock_save.return_value = mock_save_instance

        # Mock workflow execution
        mock_workflow = Mock()
        final_state = {
            "summary": {
                "meeting_id": "MTG-001",
                "title": "Test Meeting",
                "participants": ["John"],
                "summary": "Test summary"
            },
            "tasks": [
                {
                    "task_id": "TASK-001",
                    "title": "Test task",
                    "assignee": "John"
                }
            ],
            "errors": []
        }
        mock_workflow.ainvoke = AsyncMock(return_value=final_state)
        workflow_processor.workflow = mock_workflow

        # Execute workflow
        result = await workflow_processor.process(sample_text_file, ["John"])

        # Verify result
        assert isinstance(result, Meeting)
        assert result.summary.meeting_id == "MTG-001"
        assert len(result.tasks) == 1

        # Verify workflow was called
        mock_workflow.ainvoke.assert_called_once()


@pytest.mark.asyncio
async def test_workflow_process_with_errors(workflow_processor, sample_text_file):
    """Test workflow error handling"""
    with patch.object(workflow_processor.workflow, 'ainvoke', new_callable=AsyncMock) as mock_invoke:
        # Mock workflow with errors
        mock_invoke.return_value = {
            "summary": {},
            "tasks": [],
            "errors": ["Validation failed", "Missing data"]
        }

        # Should raise error
        with pytest.raises(RuntimeError, match="Processing failed"):
            await workflow_processor.process(sample_text_file)


@pytest.mark.asyncio
async def test_workflow_process_with_participants(workflow_processor, sample_text_file):
    """Test workflow with participant list"""
    participants = ["Alice", "Bob", "Charlie"]

    with patch.object(workflow_processor.workflow, 'ainvoke', new_callable=AsyncMock) as mock_invoke:
        mock_invoke.return_value = {
            "summary": {
                "meeting_id": "MTG-001",
                "participants": participants,
                "summary": "Test"
            },
            "tasks": [],
            "errors": []
        }

        result = await workflow_processor.process(sample_text_file, participants)

        assert result.summary.participants == participants


@pytest.mark.asyncio
async def test_workflow_process_with_metadata(workflow_processor, sample_text_file):
    """Test workflow with additional metadata"""
    metadata = {"source": "recorded_meeting", "duration": "30min"}

    with patch.object(workflow_processor.workflow, 'ainvoke', new_callable=AsyncMock) as mock_invoke:
        mock_invoke.return_value = {
            "summary": {
                "meeting_id": "MTG-001",
                "participants": [],
                "summary": "Test"
            },
            "tasks": [],
            "errors": [],
            "document_metadata": metadata
        }

        result = await workflow_processor.process(sample_text_file, metadata=metadata)

        assert result.metadata["document_metadata"] == metadata


def test_workflow_should_save_logic(workflow_processor):
    """Test the should_save conditional logic"""
    # Test with errors
    state_with_errors = {"errors": ["Some error"]}
    assert workflow_processor._should_save(state_with_errors) == "error"

    # Test without errors
    state_clean = {"errors": []}
    assert workflow_processor._should_save(state_clean) == "save"

    # Test with empty errors
    state_empty_errors = {"errors": None}
    assert workflow_processor._should_save(state_empty_errors) == "save"