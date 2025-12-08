"""Tests for Nominatim geocoding service."""
import pytest
from unittest.mock import AsyncMock

from app.infrastructure.geocoding.nominatim import NominatimGeocodingService
from app.infrastructure.http.http_client import HTTPClient


@pytest.mark.asyncio
async def test_geocode_success(mock_location):
    """Test successful geocoding."""
    # Mock HTTP client
    http_client = HTTPClient()
    http_client.get = AsyncMock(
        return_value=[
            {
                "lat": "47.4979",
                "lon": "19.0402",
                "display_name": "Budapest, Hungary",
            }
        ]
    )

    service = NominatimGeocodingService(
        base_url="https://nominatim.openstreetmap.org",
        http_client=http_client,
    )

    result = await service.geocode("Budapest")

    assert result.city == "Budapest"
    assert result.country == "Hungary"
    assert abs(result.coordinates.lat - 47.4979) < 0.001
    assert abs(result.coordinates.lon - 19.0402) < 0.001


@pytest.mark.asyncio
async def test_geocode_not_found():
    """Test geocoding with city not found."""
    http_client = HTTPClient()
    http_client.get = AsyncMock(return_value=[])

    service = NominatimGeocodingService(
        base_url="https://nominatim.openstreetmap.org",
        http_client=http_client,
    )

    with pytest.raises(ValueError, match="City not found"):
        await service.geocode("NonexistentCity12345")


@pytest.mark.asyncio
async def test_geocode_http_error():
    """Test geocoding with HTTP error."""
    http_client = HTTPClient()
    http_client.get = AsyncMock(side_effect=Exception("Network error"))

    service = NominatimGeocodingService(
        base_url="https://nominatim.openstreetmap.org",
        http_client=http_client,
    )

    with pytest.raises(Exception, match="Network error"):
        await service.geocode("Budapest")
