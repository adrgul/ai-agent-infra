from pydantic import BaseModel
from typing import Optional, List


class Coordinates(BaseModel):
    lat: float
    lon: float


class POI(BaseModel):
    type: str  # "park", "museum", "cafe", "viewpoint", "drinking_water", "other"
    name: str
    distance_m: int
    walking_minutes: int
    lat: float
    lon: float


class Activity(BaseModel):
    name: str
    description: str
    type: str


class CityFact(BaseModel):
    title: str
    content: str


class Briefing(BaseModel):
    paragraph: str


class CityBriefingResponse(BaseModel):
    city: str
    coordinates: Coordinates
    recommended_activities: List[Activity]
    city_facts: List[CityFact]
    briefing: Briefing
    nearby_places: List[POI] = []
    fallback_message: Optional[str] = None
    metadata: Optional[dict] = None
