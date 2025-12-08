"""Tests for briefing use case."""
from datetime import date

import pytest
from unittest.mock import AsyncMock

from app.application.briefing_usecase import BriefingUseCase


@pytest.mark.asyncio
async def test_briefing_usecase_success(
    mock_location, mock_weather_data, mock_briefing
):
    """Test successful briefing use case execution."""
    # Mock services
    geocoding_service = AsyncMock()
    geocoding_service.geocode = AsyncMock(return_value=mock_location)

    weather_service = AsyncMock()
    weather_service.get_weather = AsyncMock(return_value=mock_weather_data)

    llm_service = AsyncMock()
    llm_service.generate_briefing = AsyncMock(return_value=mock_briefing)

    history_repository = AsyncMock()
    history_repository.add_entry = AsyncMock()

    # Create use case
    usecase = BriefingUseCase(
        geocoding_service, weather_service, llm_service, history_repository
    )

    # Execute
    result = await usecase.execute("Budapest", date(2025, 11, 18))

    # Verify
    assert result.city == "Budapest"
    assert result.country == "Hungary"
    assert result.weather == mock_weather_data
    assert result.briefing == mock_briefing

    # Verify service calls
    geocoding_service.geocode.assert_called_once_with("Budapest")
    weather_service.get_weather.assert_called_once()
    llm_service.generate_briefing.assert_called_once()
    history_repository.add_entry.assert_called_once()


@pytest.mark.asyncio
async def test_briefing_usecase_geocoding_failure():
    """Test briefing use case with geocoding failure."""
    geocoding_service = AsyncMock()
    geocoding_service.geocode = AsyncMock(side_effect=ValueError("City not found"))

    weather_service = AsyncMock()
    llm_service = AsyncMock()
    history_repository = AsyncMock()

    usecase = BriefingUseCase(
        geocoding_service, weather_service, llm_service, history_repository
    )

    with pytest.raises(ValueError, match="City not found"):
        await usecase.execute("NonexistentCity", date(2025, 11, 18))

    # Verify no further services were called
    weather_service.get_weather.assert_not_called()
    llm_service.generate_briefing.assert_not_called()
