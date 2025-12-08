"""Test configuration and fixtures."""
import pytest


@pytest.fixture
def mock_coordinates():
    """Mock coordinates."""
    return {"lat": 47.4979, "lon": 19.0402}


@pytest.fixture
def mock_location(mock_coordinates):
    """Mock location data."""
    from app.domain.models import Coordinates, Location

    return Location(
        city="Budapest",
        country="Hungary",
        coordinates=Coordinates(**mock_coordinates),
    )


@pytest.fixture
def mock_weather_data():
    """Mock weather data."""
    from app.domain.models import WeatherData

    return WeatherData(
        temperature_min=8.5,
        temperature_max=14.2,
        wind_speed=3.5,
        precipitation_probability=20,
    )


@pytest.fixture
def mock_briefing():
    """Mock AI briefing."""
    from app.domain.models import Briefing

    return Briefing(
        summary="Mild autumn day with partly cloudy skies.",
        outfit="Layer up with a light jacket and comfortable shoes.",
        activities=[
            "Walk along the Danube",
            "Visit a museum",
            "Enjoy coffee at a café",
        ],
        note=None,
    )
