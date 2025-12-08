"""Tests for OpenAI LLM service."""
from datetime import date

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.infrastructure.llm.openai_llm import OpenAILLMService


@pytest.mark.asyncio
async def test_generate_briefing_success(mock_weather_data, mock_briefing):
    """Test successful briefing generation."""
    # Mock OpenAI client
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content='{"summary": "Mild autumn day with partly cloudy skies.", '
                '"outfit": "Layer up with a light jacket and comfortable shoes.", '
                '"activities": ["Walk along the Danube", "Visit a museum", "Enjoy coffee at a café"], '
                '"note": null}'
            )
        )
    ]

    service = OpenAILLMService(api_key="test-key", model="gpt-4o-mini")
    service.client.chat.completions.create = AsyncMock(return_value=mock_response)

    result = await service.generate_briefing(
        "Budapest", "Hungary", date(2025, 11, 18), mock_weather_data
    )

    assert result.summary == mock_briefing.summary
    assert result.outfit == mock_briefing.outfit
    assert len(result.activities) == 3
    assert result.note is None


@pytest.mark.asyncio
async def test_generate_briefing_with_note(mock_weather_data):
    """Test briefing generation for future date with uncertainty note."""
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content='{"summary": "Weather forecast.", '
                '"outfit": "Dress accordingly.", '
                '"activities": ["Activity 1", "Activity 2", "Activity 3"], '
                '"note": "Forecast is 10 days ahead, uncertainty is higher."}'
            )
        )
    ]

    service = OpenAILLMService(api_key="test-key", model="gpt-4o-mini")
    service.client.chat.completions.create = AsyncMock(return_value=mock_response)

    # Date 10 days in future
    from datetime import timedelta

    future_date = date.today() + timedelta(days=10)

    result = await service.generate_briefing(
        "Budapest", "Hungary", future_date, mock_weather_data
    )

    assert result.note is not None
    assert "uncertainty" in result.note.lower()


@pytest.mark.asyncio
async def test_generate_briefing_invalid_json(mock_weather_data):
    """Test briefing generation with invalid JSON (should retry)."""
    # First call returns invalid JSON, second call succeeds
    mock_response_invalid = MagicMock()
    mock_response_invalid.choices = [
        MagicMock(message=MagicMock(content='{"invalid": "json"}'))
    ]

    mock_response_valid = MagicMock()
    mock_response_valid.choices = [
        MagicMock(
            message=MagicMock(
                content='{"summary": "Test", "outfit": "Test", '
                '"activities": ["A1", "A2", "A3"], "note": null}'
            )
        )
    ]

    service = OpenAILLMService(api_key="test-key", model="gpt-4o-mini")
    service.client.chat.completions.create = AsyncMock(
        side_effect=[mock_response_invalid, mock_response_valid]
    )

    result = await service.generate_briefing(
        "Budapest", "Hungary", date(2025, 11, 18), mock_weather_data
    )

    assert result.summary == "Test"
    assert len(result.activities) == 3
