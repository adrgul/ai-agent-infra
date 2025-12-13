"""
Tests for the summarizer agent
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from meetingai.agents.summarizer import SummarizerAgent
from meetingai.models.meeting import MeetingSummary


@pytest.fixture
def summarizer(sample_config):
    return SummarizerAgent(sample_config)


@pytest.mark.asyncio
async def test_summarizer_initialization(summarizer, sample_config):
    """Test summarizer agent initialization"""
    assert summarizer.config == sample_config
    assert summarizer.llm is not None
    assert summarizer.prompt_template is not None


@pytest.mark.asyncio
async def test_summarize_basic(summarizer, sample_transcript):
    """Test basic summarization functionality"""
    with patch.object(summarizer.llm, 'ainvoke', new_callable=AsyncMock) as mock_invoke:
        # Mock LLM response
        mock_response = Mock()
        mock_response.content = """
        Team discussed Q4 priorities including login feature and performance optimization.
        Key decisions: Login feature is P1, Performance audit needed.
        Next steps: UI mockup review, Backend API setup.
        """
        mock_invoke.return_value = mock_response

        # Call summarize
        result = await summarizer.summarize(sample_transcript, ["John", "Peter", "Maria"])

        # Verify result
        assert isinstance(result, MeetingSummary)
        assert result.participants == ["John", "Peter", "Maria"]
        assert "login" in result.summary.lower()
        assert "Q4" in result.summary

        # Verify LLM was called
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
async def test_summarize_empty_transcript(summarizer):
    """Test error handling for empty transcript"""
    with pytest.raises(ValueError, match="Transcript cannot be empty"):
        await summarizer.summarize("", [])


@pytest.mark.asyncio
async def test_summarize_llm_error(summarizer):
    """Test error handling when LLM fails"""
    with patch.object(summarizer.llm, 'ainvoke', side_effect=Exception("API Error")):
        with pytest.raises(RuntimeError, match="Failed to generate summary"):
            await summarizer.summarize("Valid transcript", [])


@pytest.mark.asyncio
async def test_summarize_with_participants(summarizer, sample_transcript):
    """Test summarization with participant list"""
    participants = ["Alice", "Bob", "Charlie"]

    with patch.object(summarizer.llm, 'ainvoke', new_callable=AsyncMock) as mock_invoke:
        mock_response = Mock()
        mock_response.content = "Meeting summary content"
        mock_invoke.return_value = mock_response

        result = await summarizer.summarize(sample_transcript, participants)

        assert result.participants == participants
        # Verify participants were included in prompt
        call_args = mock_invoke.call_args[0][0]
        assert "Alice" in call_args
        assert "Bob" in call_args
        assert "Charlie" in call_args