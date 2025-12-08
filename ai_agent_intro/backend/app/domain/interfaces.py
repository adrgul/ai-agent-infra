"""Domain interfaces (protocols) for dependency inversion."""
from datetime import date
from typing import Optional, Protocol

from app.domain.models import Briefing, HistoryEntry, Location, UserProfile, WeatherData


class GeocodingService(Protocol):
    """Protocol for geocoding services."""

    async def geocode(self, city: str) -> Location:
        """
        Geocode a city name to location with coordinates.

        Args:
            city: City name to geocode

        Returns:
            Location with city, country, and coordinates

        Raises:
            Exception: If geocoding fails
        """
        ...


class WeatherService(Protocol):
    """Protocol for weather services."""

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
            Exception: If weather fetch fails
        """
        ...


class LLMService(Protocol):
    """Protocol for LLM services."""

    async def generate_briefing(
        self,
        city: str,
        country: str,
        target_date: date,
        weather: WeatherData,
        user_profile: Optional[UserProfile] = None,
    ) -> Briefing:
        """
        Generate a daily briefing using LLM.

        Args:
            city: City name
            country: Country name
            target_date: Target date
            weather: Weather data
            user_profile: Optional user profile for personalization

        Returns:
            AI-generated briefing

        Raises:
            Exception: If briefing generation fails
        """
        ...


class HistoryRepository(Protocol):
    """Protocol for history persistence."""

    async def add_entry(self, entry: HistoryEntry) -> None:
        """
        Add a history entry.

        Args:
            entry: History entry to add
        """
        ...

    async def get_recent(self, limit: int = 20) -> list[HistoryEntry]:
        """
        Get recent history entries.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of recent history entries
        """
        ...


class UserProfileRepository(Protocol):
    """Protocol for user profile persistence."""

    async def get_profile(self) -> Optional[UserProfile]:
        """
        Get the user profile.

        Returns:
            User profile if exists, None otherwise
        """
        ...

    async def save_profile(self, profile: UserProfile) -> None:
        """
        Save or update the user profile.

        Args:
            profile: User profile to save
        """
        ...
