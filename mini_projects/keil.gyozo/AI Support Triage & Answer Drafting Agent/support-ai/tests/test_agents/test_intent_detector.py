"""
Tests for intent detector agent.
"""

import pytest
from unittest.mock import AsyncMock, patch

from src.agents.intent_detector import detect_intent
from src.workflow.state import WorkflowState


class TestIntentDetector:
    """Test cases for intent detection."""

    @pytest.mark.asyncio
    async def test_billing_issue_detection(self):
        """Test detection of billing-related issues."""
        state: WorkflowState = {
            "ticket_id": "TKT-001",
            "original_message": "I was charged twice for my subscription!",
            "errors": []
        }

        # Mock LLM response
        mock_response = AsyncMock()
        mock_response.content = '{"problem_type": "billing", "sentiment": "frustrated", "confidence": 0.9, "reasoning": "Contains billing keywords"}'

        with patch('src.agents.intent_detector.ChatOpenAI') as mock_llm_class:
            mock_llm = AsyncMock()
            mock_llm_class.return_value = mock_llm

            mock_chain = AsyncMock()
            mock_chain.ainvoke.return_value = mock_response
            mock_llm.return_value = mock_chain

            result = await detect_intent(state)

            assert "intent" in result
            assert result["intent"]["problem_type"] == "billing"
            assert result["intent"]["sentiment"] == "frustrated"
            assert result["intent"]["confidence"] == 0.9

    @pytest.mark.asyncio
    async def test_technical_issue_detection(self):
        """Test detection of technical issues."""
        state: WorkflowState = {
            "ticket_id": "TKT-002",
            "original_message": "The login page is not loading properly.",
            "errors": []
        }

        mock_response = AsyncMock()
        mock_response.content = '{"problem_type": "technical", "sentiment": "neutral", "confidence": 0.85, "reasoning": "Technical login issue"}'

        with patch('src.agents.intent_detector.ChatOpenAI') as mock_llm_class:
            mock_llm_class.return_value = AsyncMock()
            mock_chain = AsyncMock()
            mock_chain.ainvoke.return_value = mock_response

            # Mock the chain creation
            with patch('src.agents.intent_detector.ChatPromptTemplate.from_template') as mock_template:
                mock_template.return_value = mock_chain

                result = await detect_intent(state)

                assert result["intent"]["problem_type"] == "technical"
                assert result["intent"]["sentiment"] == "neutral"

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling when LLM fails."""
        state: WorkflowState = {
            "ticket_id": "TKT-003",
            "original_message": "Some message",
            "errors": []
        }

        with patch('src.agents.intent_detector.ChatOpenAI') as mock_llm_class:
            mock_llm_class.side_effect = Exception("API Error")

            result = await detect_intent(state)

            assert "intent" in result
            assert result["intent"]["problem_type"] == "other"
            assert result["intent"]["sentiment"] == "neutral"
            assert len(result["errors"]) > 0