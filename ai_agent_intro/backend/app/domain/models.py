"""Domain models representing business entities."""
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class Coordinates(BaseModel):
    """Geographic coordinates."""

    lat: float = Field(..., description="Latitude")
    lon: float = Field(..., description="Longitude")


class Location(BaseModel):
    """Location information."""

    city: str = Field(..., description="City name")
    country: str = Field(..., description="Country name")
    coordinates: Coordinates = Field(..., description="Geographic coordinates")


class WeatherData(BaseModel):
    """Weather forecast data."""

    temperature_min: float = Field(..., description="Minimum temperature in Celsius")
    temperature_max: float = Field(..., description="Maximum temperature in Celsius")
    wind_speed: float = Field(..., description="Wind speed in m/s")
    precipitation_probability: int = Field(
        ..., ge=0, le=100, description="Precipitation probability percentage"
    )


class Briefing(BaseModel):
    """AI-generated daily briefing."""

    summary: str = Field(..., description="Weather summary")
    outfit: str = Field(..., description="Outfit recommendation")
    activities: list[str] = Field(
        ..., min_length=3, max_length=3, description="Activity suggestions"
    )
    note: Optional[str] = Field(None, description="Additional note")


class BriefingResponse(BaseModel):
    """Complete briefing response."""

    city: str
    country: str
    coordinates: Coordinates
    date: date
    weather: WeatherData
    briefing: Briefing
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HistoryEntry(BaseModel):
    """History entry for persistence."""

    city: str
    date: date
    timestamp: datetime


class UserProfile(BaseModel):
    """User profile for personalized recommendations."""

    age: Optional[int] = Field(None, ge=1, le=120, description="User age")
    interests: list[str] = Field(
        default_factory=list,
        description="User interests (e.g., hiking, museums, cafes, sports)",
    )
    mobility: Optional[str] = Field(
        None,
        description="Mobility level: high, medium, or low",
        pattern="^(high|medium|low)$",
    )
    clothing_style: Optional[str] = Field(
        None,
        description="Preferred clothing style: casual, formal, or sporty",
        pattern="^(casual|formal|sporty)$",
    )
    dietary_preferences: list[str] = Field(
        default_factory=list,
        description="Dietary preferences (e.g., vegetarian, vegan, gluten-free)",
    )

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "age": 30,
                "interests": ["hiking", "museums", "photography"],
                "mobility": "high",
                "clothing_style": "casual",
                "dietary_preferences": ["vegetarian"],
            }
        }
