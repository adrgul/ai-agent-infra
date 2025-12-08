"""Dependency injection container (composition root)."""
from app.application.briefing_usecase import BriefingUseCase
from app.application.briefing_usecase_langgraph import BriefingUseCaseLangGraph
from app.config.settings import Settings
from app.infrastructure.geocoding.nominatim import NominatimGeocodingService
from app.infrastructure.http.http_client import HTTPClient
from app.infrastructure.llm.openai_llm import OpenAILLMService
from app.infrastructure.persistence.file_history import FileHistoryRepository
from app.infrastructure.persistence.profile_repository import FileUserProfileRepository
from app.infrastructure.weather.openmeteo import OpenMeteoWeatherService


class Container:
    """Dependency injection container."""

    def __init__(self, settings: Settings, use_langgraph: bool = True):
        """
        Initialize container with settings.

        Args:
            settings: Application settings
            use_langgraph: Whether to use LangGraph agent (default: True)
        """
        self.settings = settings
        self.use_langgraph = use_langgraph

        # Infrastructure
        self.http_client = HTTPClient()
        self.geocoding_service = NominatimGeocodingService(
            settings.nominatim_base, self.http_client
        )
        self.weather_service = OpenMeteoWeatherService(
            settings.openmeteo_base, self.http_client
        )
        self.llm_service = OpenAILLMService(
            settings.openai_api_key, settings.openai_model
        )
        self.history_repository = FileHistoryRepository(settings.data_dir)
        self.profile_repository = FileUserProfileRepository(settings.data_dir)

        # Application - choose between LangGraph and traditional
        if use_langgraph:
            self.briefing_usecase = BriefingUseCaseLangGraph(
                self.geocoding_service,
                self.weather_service,
                self.history_repository,
                self.profile_repository,
                settings.openai_api_key,
                settings.openai_model,
            )
        else:
            self.briefing_usecase = BriefingUseCase(
                self.geocoding_service,
                self.weather_service,
                self.llm_service,
                self.history_repository,
                self.profile_repository,
            )


def create_container(settings: Settings, use_langgraph: bool = True) -> Container:
    """
    Create and configure the dependency injection container.

    Args:
        settings: Application settings
        use_langgraph: Whether to use LangGraph agent

    Returns:
        Configured container
    """
    return Container(settings, use_langgraph=use_langgraph)
