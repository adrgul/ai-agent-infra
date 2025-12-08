"""Open-Meteo weather service implementation."""
from datetime import date, timedelta

from loguru import logger

from app.domain.models import WeatherData
from app.infrastructure.http.http_client import HTTPClient


class OpenMeteoWeatherService:
    """Weather service using Open-Meteo API."""

    def __init__(self, base_url: str, http_client: HTTPClient):
        """
        Initialize Open-Meteo weather service.

        Args:
            base_url: Open-Meteo API base URL
            http_client: HTTP client instance
        """
        self.base_url = base_url.rstrip("/")
        self.http_client = http_client

    async def get_weather(
        self, latitude: float, longitude: float, target_date: date
    ) -> WeatherData:
        """
        Get weather forecast for a location and date.

        Args:
            latitude: Location latitude
            longitude: Location longitude
            target_date: Date to get forecast for

        Returns:
            Weather data for the specified date

        Raises:
            ValueError: If date is out of range or data not available
            Exception: If weather fetch fails
        """
        # Open-Meteo free API provides forecasts up to 7 days ahead
        days_ahead = (target_date - date.today()).days
        if days_ahead < 0 or days_ahead > 7:
            raise ValueError(
                f"Date must be within next 7 days. Requested: {target_date}"
            )

        url = f"{self.base_url}/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "daily": "temperature_2m_min,temperature_2m_max,windspeed_10m_max,precipitation_probability_max",
            "timezone": "auto",
            "start_date": target_date.isoformat(),
            "end_date": target_date.isoformat(),
        }

        logger.info(f"Fetching weather for {latitude}, {longitude} on {target_date}")

        try:
            async with self.http_client as client:
                data = await client.get(url, params=params)

            daily = data.get("daily", {})
            
            if not daily or not daily.get("time"):
                raise ValueError("No weather data available for the specified date")

            # Extract data for the target date
            idx = 0  # Should be the only date in response
            
            weather = WeatherData(
                temperature_min=daily["temperature_2m_min"][idx],
                temperature_max=daily["temperature_2m_max"][idx],
                wind_speed=daily["windspeed_10m_max"][idx],
                precipitation_probability=int(
                    daily.get("precipitation_probability_max", [0])[idx] or 0
                ),
            )

            logger.info(
                f"Weather: {weather.temperature_min}°C - {weather.temperature_max}°C, "
                f"wind {weather.wind_speed} m/s, precipitation {weather.precipitation_probability}%"
            )

            return weather

        except Exception as e:
            logger.error(f"Weather fetch failed: {e}")
            raise
