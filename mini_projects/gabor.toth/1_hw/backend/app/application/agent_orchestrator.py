from .briefing_service import BriefingService
from ..domain.models import CityBriefingResponse


class AgentOrchestrator:
    """Simple orchestrator without LangGraph (can be extended with LangGraph later)."""
    
    def __init__(self, briefing_service: BriefingService):
        self.briefing_service = briefing_service

    async def execute(
        self,
        city: str,
        activity: str = None,
    ) -> CityBriefingResponse:
        """Execute the briefing generation pipeline."""
        return await self.briefing_service.generate_briefing(
            city=city,
            activity=activity,
        )
