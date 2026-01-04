from abc import ABC, abstractmethod
from typing import Optional
from .models import Coordinates, POI, CityFact, Activity


class GeocodingPort(ABC):
    @abstractmethod
    async def get_coordinates(self, city: str) -> Coordinates:
        pass


class PlacesPort(ABC):
    @abstractmethod
    async def get_nearby_places(
        self, 
        coordinates: Coordinates, 
        radius_m: int = 2000, 
        limit: int = 5, 
        poi_types: Optional[list[str]] = None,
        activity: Optional[str] = None,
        city_name: Optional[str] = None
    ) -> list[POI]:
        pass


class KnowledgePort(ABC):
    @abstractmethod
    async def get_city_facts(self, city: str, activity: str = None, limit: int = 3) -> list[CityFact]:
        pass


class LLMPort(ABC):
    @abstractmethod
    async def generate_briefing(self, city: str, context: dict) -> str:
        pass


class HistoryPort(ABC):
    @abstractmethod
    async def save_briefing(self, briefing_data: dict) -> None:
        pass

    @abstractmethod
    async def get_history(self, limit: int) -> list[dict]:
        pass
