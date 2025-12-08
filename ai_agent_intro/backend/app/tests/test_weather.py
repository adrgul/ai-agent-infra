"""Tests for Open-Meteo weather service."""
from datetime import date, timedelta

import pytest
from unittest.mock import AsyncMock

from app.infrastructure.http.http_client import HTTPClient
from app.infrastructure.weather.openmeteo import OpenMeteoWeatherService


@pytest.mark.asyncio
async def test_get_weather_success(mock_weather_data):
    """Test successful weather fetch."""
    http_client = HTTPClient()
    http_client.get = AsyncMock(
        return_value={
            "daily": {
                "time": ["2025-11-18"],
                "temperature_2m_min": [8.5],
                "temperature_2m_max": [14.2],
                "windspeed_10m_max": [3.5],
                "precipitation_probability_max": [20],
            }
        }
    )

    service = OpenMeteoWeatherService(
        base_url="https://api.open-meteo.com/v1",
        http_client=http_client,
    )

    target_date = date.today() + timedelta(days=1)
    result = await service.get_weather(47.4979, 19.0402, target_date)

    assert result.temperature_min == 8.5
    assert result.temperature_max == 14.2
    assert result.wind_speed == 3.5
    assert result.precipitation_probability == 20


@pytest.mark.asyncio
async def test_get_weather_date_out_of_range():
    """Test weather fetch with date out of range."""
    http_client = HTTPClient()

    service = OpenMeteoWeatherService(
        base_url="https://api.open-meteo.com/v1",
        http_client=http_client,
    )

    # Date too far in the future
    target_date = date.today() + timedelta(days=20)

    with pytest.raises(ValueError, match="Date must be within next 16 days"):
        await service.get_weather(47.4979, 19.0402, target_date)


@pytest.mark.asyncio
async def test_get_weather_no_data():
    """Test weather fetch with no data available."""
    http_client = HTTPClient()
    http_client.get = AsyncMock(return_value={"daily": {}})

    service = OpenMeteoWeatherService(
        base_url="https://api.open-meteo.com/v1",
        http_client=http_client,
    )

    target_date = date.today() + timedelta(days=1)

    with pytest.raises(ValueError, match="No weather data available"):
        await service.get_weather(47.4979, 19.0402, target_date)
