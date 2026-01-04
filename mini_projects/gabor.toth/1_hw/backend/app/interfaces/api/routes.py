from fastapi import APIRouter, Query
import os
import sys
from ...domain.models import CityBriefingResponse
from ...application.agent_orchestrator import AgentOrchestrator
from ...application.briefing_service import BriefingService
from ...infrastructure.geocoding.nominatim import NominatimGeocoder
from ...infrastructure.places.overpass import OverpassClient
from ...infrastructure.knowledge.wikipedia import WikipediaClient
from ...infrastructure.llm.openai_llm import OpenAIClient
from ...infrastructure.persistence.history_repo import FileHistoryRepository

router = APIRouter(prefix="/api", tags=["briefing"])

# Initialize dependencies
geocoding = NominatimGeocoder()
places = OverpassClient()  # Use OpenStreetMap/Overpass
knowledge = WikipediaClient()
llm = OpenAIClient()
history = FileHistoryRepository()

briefing_service = BriefingService(
    geocoding=geocoding,
    places=places,
    knowledge=knowledge,
    llm=llm,
    history=history,
)

orchestrator = AgentOrchestrator(briefing_service)


@router.get("/briefing", response_model=CityBriefingResponse)
async def get_briefing(
    city: str = Query(..., description="City name"),
    activity: str = Query(None, description="Desired activity (e.g., hiking, museums, coffee)"),
):
    """Generate a city briefing with city facts and briefing text."""
    print(f"🔄 [API] Starting briefing generation for: {city}")
    print(f"   Parameters: activity={activity}")
    
    try:
        result = await orchestrator.execute(
            city=city,
            activity=activity,
        )
        print(f"✅ [API] Successfully generated briefing for: {city}")
        return result
    except Exception as e:
        print(f"❌ [API] Error generating briefing: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


@router.get("/history")
async def get_history(limit: int = Query(20, description="Number of entries")):
    """Get briefing history."""
    return await history.get_history(limit=limit)

@router.post("/shutdown")
async def shutdown():
    """Shutdown the server."""
    print("🛑 [API] Shutdown request received")
    
    # Felszabadítás és leállítás egy másik threadben
    import threading
    def stop_server():
        import time
        time.sleep(1)
        print("🛑 [API] Stopping server...")
        os.kill(os.getpid(), 15)  # SIGTERM
    
    thread = threading.Thread(target=stop_server, daemon=True)
    thread.start()
    
    return {"status": "shutting down"}