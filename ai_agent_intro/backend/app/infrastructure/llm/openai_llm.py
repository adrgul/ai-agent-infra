"""OpenAI LLM service implementation."""
import json
from datetime import date
from typing import Optional

from loguru import logger
from openai import AsyncOpenAI
from pydantic import ValidationError
from tenacity import retry, retry_if_exception_type, stop_after_attempt

from app.domain.models import Briefing, UserProfile, WeatherData


class OpenAILLMService:
    """LLM service using OpenAI API."""

    def __init__(self, api_key: str, model: str):
        """
        Initialize OpenAI LLM service.

        Args:
            api_key: OpenAI API key
            model: Model name to use
        """
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    def _build_prompt(
        self,
        city: str,
        country: str,
        target_date: date,
        weather: WeatherData,
        user_profile: Optional[UserProfile] = None,
    ) -> str:
        """Build the LLM prompt."""
        days_ahead = (target_date - date.today()).days

        # Build personalization context
        personalization = ""
        if user_profile:
            parts = []
            if user_profile.age:
                parts.append(f"Age: {user_profile.age}")
            if user_profile.interests:
                parts.append(f"Interests: {', '.join(user_profile.interests)}")
            if user_profile.mobility:
                parts.append(f"Mobility: {user_profile.mobility}")
            if user_profile.clothing_style:
                parts.append(f"Style: {user_profile.clothing_style}")
            if user_profile.dietary_preferences:
                parts.append(
                    f"Dietary: {', '.join(user_profile.dietary_preferences)}"
                )

            if parts:
                personalization = f"\nUser Profile:\n- " + "\n- ".join(parts) + "\n"

        return f"""Role: Weather day-planner AI assistant with local knowledge.

Input:
- City: {city} ({country})
- Date: {target_date.isoformat()}
- Weather: min {weather.temperature_min}°C, max {weather.temperature_max}°C, wind {weather.wind_speed} m/s, precipitation probability {weather.precipitation_probability}%
{personalization}
Task:
- Write a short 1–2 sentence weather summary.
- Provide concise outfit advice{' tailored to the user profile' if user_profile else ''}.
- Suggest exactly 3 **SPECIFIC** activities with REAL venue names and addresses in {city}:
  * At least 1 outdoor activity (with specific location/park/area name)
  * At least 1 indoor activity (specific café/restaurant/museum/theater with name and address)
  * Each suggestion MUST include: venue name, street address, and brief reason why
  * {'Match venues to user interests (e.g., vegan restaurants for vegan dietary preferences, live music venues for music interests)' if user_profile else 'Choose popular, well-known venues'}
- If the date is more than 7 days in the future, add a one-sentence uncertainty note.

IMPORTANT: Do NOT give generic suggestions like "Visit a local café" or "Check out a theater". 
Instead, provide REAL venues like "Café de Jaren (Nieuwe Doelenstraat 20) - cozy spot with canal views and vegan options".

Return **strict JSON** in the following schema:
{{
  "summary": string,
  "outfit": string,
  "activities": [string, string, string],
  "note": string | null
}}

{"Note: The forecast is " + str(days_ahead) + " days ahead, so uncertainty is higher." if days_ahead > 7 else ""}
"""

    @retry(
        retry=retry_if_exception_type(ValidationError),
        stop=stop_after_attempt(2),
        reraise=True,
    )
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
            ValidationError: If JSON response is invalid (retries once)
        """
        prompt = self._build_prompt(city, country, target_date, weather, user_profile)

        logger.info(
            f"Generating briefing for {city}, {country} on {target_date}"
            + (" (personalized)" if user_profile else " (generic)")
        )

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful weather assistant that provides briefings in strict JSON format.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from LLM")

            # Parse and validate JSON
            data = json.loads(content)
            briefing = Briefing(**data)

            logger.info("Briefing generated successfully")

            return briefing

        except ValidationError as e:
            logger.warning(f"Invalid JSON from LLM, retrying: {e}")
            raise
        except Exception as e:
            logger.error(f"Briefing generation failed: {e}")
            raise
