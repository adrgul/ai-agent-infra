"""Briefing use case - orchestrates the entire workflow."""
from datetime import date, datetime
from typing import Optional

from loguru import logger

from app.application.agent_plan import AgentPlanner, AgentState
from app.domain.interfaces import (
    GeocodingService,
    HistoryRepository,
    LLMService,
    UserProfileRepository,
    WeatherService,
)
from app.domain.models import BriefingResponse, HistoryEntry, UserProfile


class BriefingUseCase:
    """Use case for generating weather briefings."""

    def __init__(
        self,
        geocoding_service: GeocodingService,
        weather_service: WeatherService,
        llm_service: LLMService,
        history_repository: HistoryRepository,
        profile_repository: UserProfileRepository,
    ):
        """
        Initialize briefing use case.

        Args:
            geocoding_service: Service for geocoding
            weather_service: Service for weather data
            llm_service: Service for LLM briefings
            history_repository: Repository for history
            profile_repository: Repository for user profile
        """
        self.geocoding_service = geocoding_service
        self.weather_service = weather_service
        self.llm_service = llm_service
        self.history_repository = history_repository
        self.profile_repository = profile_repository

    async def execute(self, city: str, target_date: date) -> BriefingResponse:
        """
        Execute the briefing use case.

        This implements the agent loop:
        Goal → Plan → Act (tools) → Observe → Reflect

        Args:
            city: City name
            target_date: Target date

        Returns:
            Complete briefing response

        Raises:
            Exception: If any step fails
        """
        # GOAL & PLAN
        plan = AgentPlanner.create_briefing_plan(city, target_date)
        logger.info(f"Executing plan: {plan.goal}")

        # Get user profile
        user_profile = await self.profile_repository.get_profile()
        if user_profile:
            logger.info("Using personalized user profile")

        try:
            # ACT: Step 1 - Geocode
            plan.state = AgentState.GEOCODING
            step = plan.next_step()
            logger.info(f"Step {plan.current_step}/{len(plan.steps)}: {step}")

            location = await self.geocoding_service.geocode(city)

            # OBSERVE
            logger.info(
                f"Geocoded to: {location.city}, {location.country} "
                f"({location.coordinates.lat}, {location.coordinates.lon})"
            )

            # ACT: Step 2 - Fetch weather
            plan.state = AgentState.FETCHING_WEATHER
            step = plan.next_step()
            logger.info(f"Step {plan.current_step}/{len(plan.steps)}: {step}")

            weather = await self.weather_service.get_weather(
                location.coordinates.lat,
                location.coordinates.lon,
                target_date,
            )

            # OBSERVE
            logger.info(
                f"Weather: {weather.temperature_min}-{weather.temperature_max}°C, "
                f"{weather.precipitation_probability}% precipitation"
            )

            # ACT: Step 3 - Generate briefing
            plan.state = AgentState.GENERATING_BRIEFING
            step = plan.next_step()
            logger.info(f"Step {plan.current_step}/{len(plan.steps)}: {step}")

            briefing = await self.llm_service.generate_briefing(
                location.city,
                location.country,
                target_date,
                weather,
                user_profile,
            )

            # OBSERVE
            logger.info(f"Generated briefing with {len(briefing.activities)} activities")

            # ACT: Step 4 - Save to history
            step = plan.next_step()
            logger.info(f"Step {plan.current_step}/{len(plan.steps)}: {step}")

            history_entry = HistoryEntry(
                city=location.city,
                date=target_date,
                timestamp=datetime.utcnow(),
            )
            await self.history_repository.add_entry(history_entry)

            # REFLECT
            plan.state = AgentState.COMPLETED
            logger.info("Plan completed successfully")

            return BriefingResponse(
                city=location.city,
                country=location.country,
                coordinates=location.coordinates,
                date=target_date,
                weather=weather,
                briefing=briefing,
                timestamp=datetime.utcnow(),
            )

        except Exception as e:
            plan.state = AgentState.FAILED
            logger.error(f"Plan failed at step {plan.current_step}: {e}")
            raise
