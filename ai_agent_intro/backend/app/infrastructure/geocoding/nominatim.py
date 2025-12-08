"""Nominatim geocoding service implementation."""
from loguru import logger

from app.domain.models import Coordinates, Location
from app.infrastructure.http.http_client import HTTPClient


class NominatimGeocodingService:
    """Geocoding service using OpenStreetMap Nominatim."""

    USER_AGENT = "AIWeatherAgent/1.0"

    def __init__(self, base_url: str, http_client: HTTPClient):
        """
        Initialize Nominatim geocoding service.

        Args:
            base_url: Nominatim API base URL
            http_client: HTTP client instance
        """
        self.base_url = base_url.rstrip("/")
        self.http_client = http_client

    async def geocode(self, city: str) -> Location:
        """
        Geocode a city name to location with coordinates.

        Args:
            city: City name to geocode

        Returns:
            Location with city, country, and coordinates

        Raises:
            ValueError: If city not found
            Exception: If geocoding fails
        """
        url = f"{self.base_url}/search"
        params = {
            "q": city,
            "format": "json",
            "limit": 1,
        }
        headers = {
            "User-Agent": self.USER_AGENT,
        }

        logger.info(f"Geocoding city: {city}")

        try:
            async with self.http_client as client:
                results = await client.get(url, params=params, headers=headers)

            if not results:
                raise ValueError(f"City not found: {city}")

            result = results[0]

            location = Location(
                city=result.get("display_name", "").split(",")[0].strip(),
                country=result.get("display_name", "").split(",")[-1].strip(),
                coordinates=Coordinates(
                    lat=float(result["lat"]),
                    lon=float(result["lon"]),
                ),
            )

            logger.info(
                f"Geocoded {city} to {location.coordinates.lat}, {location.coordinates.lon}"
            )

            return location

        except Exception as e:
            logger.error(f"Geocoding failed for {city}: {e}")
            raise
