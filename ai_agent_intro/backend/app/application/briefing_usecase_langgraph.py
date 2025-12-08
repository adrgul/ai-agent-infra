"""Briefing use case with LangGraph agent option."""
from datetime import date, datetime

from loguru import logger

from app.application.langgraph_agent import LangGraphWeatherAgent
from app.domain.interfaces import (
    GeocodingService,
    HistoryRepository,
    LLMService,
    UserProfileRepository,
    WeatherService,
)
from app.domain.models import BriefingResponse, HistoryEntry


class BriefingUseCaseLangGraph:
    """Use case for generating weather briefings with LangGraph agent."""

    def __init__(
        self,
        geocoding_service: GeocodingService,
        weather_service: WeatherService,
        history_repository: HistoryRepository,
        profile_repository: UserProfileRepository,
        llm_api_key: str,
        llm_model: str,
    ):
        """
        Initialize briefing use case with LangGraph agent.

        Args:
            geocoding_service: Service for geocoding
            weather_service: Service for weather data
            history_repository: Repository for history
            profile_repository: Repository for user profile
            llm_api_key: OpenAI API key
            llm_model: Model name to use
        """
        self.history_repository = history_repository
        self.profile_repository = profile_repository

        # Create LangGraph agent
        self.agent = LangGraphWeatherAgent(
            geocoding_service=geocoding_service,
            weather_service=weather_service,
            llm_api_key=llm_api_key,
            llm_model=llm_model,
        )

    async def execute(self, city: str, target_date: date, language: str | None = None) -> BriefingResponse:
        """
        Execute the briefing use case using LangGraph agent.

        Args:
            city: City name
            target_date: Target date
            language: Language code for the response (e.g., 'en', 'es', 'fr')

        Returns:
            Complete briefing response

        Raises:
            Exception: If any step fails
        """
        logger.info(f"[USE CASE] Executing LangGraph workflow for {city} on {target_date} (language: {language or 'en'})")

        # Get user profile
        user_profile = await self.profile_repository.get_profile()
        if user_profile:
            logger.info("[USE CASE] Using personalized user profile")

        try:
            # Run the LangGraph agent
            result = await self.agent.run(city, target_date, user_profile, language)

            # Save to history
            history_entry = HistoryEntry(
                city=result.city,
                date=target_date,
                timestamp=datetime.utcnow(),
            )
            await self.history_repository.add_entry(history_entry)

            logger.info(f"[USE CASE] LangGraph workflow completed successfully")

            return result

        except Exception as e:
            logger.error(f"[USE CASE] LangGraph workflow failed: {e}")
            raise
