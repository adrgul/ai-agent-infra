"""
API layer - FastAPI application with endpoints.
Following SOLID: 
- Single Responsibility - Controllers are thin, delegate to services.
- Dependency Inversion - Controllers depend on service abstractions.
"""
import os
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from domain.models import ChatRequest, ChatResponse, ProfileUpdateRequest
from domain.interfaces import IUserRepository, IConversationRepository
from infrastructure.repositories import FileUserRepository, FileConversationRepository
from infrastructure.tool_clients import (
    OpenMeteoWeatherClient, NominatimGeocodeClient, IPAPIGeolocationClient,
    ExchangeRateHostClient, CoinGeckoCryptoClient
)
from services.tools import (
    HistorySearchTool, DailyAdviceTool
)
from services.agent import AIAgent
from services.chat_service import ChatService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global service instances
chat_service: ChatService = None
user_repo: IUserRepository = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager - initialize services on startup."""
    global chat_service, user_repo
    
    logger.info("Initializing application...")
    
    # Get OpenAI API key
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        logger.error("OPENAI_API_KEY environment variable not set!")
        raise RuntimeError("OPENAI_API_KEY must be set")
    
    # Initialize repositories
    user_repo = FileUserRepository(data_dir="data/users")
    conversation_repo = FileConversationRepository(data_dir="data/sessions")
    
    # Initialize tool clients
    geocode_client = NominatimGeocodeClient()
    weather_client = OpenMeteoWeatherClient(geocode_client)
    ip_client = IPAPIGeolocationClient()
    fx_client = ExchangeRateHostClient()
    crypto_client = CoinGeckoCryptoClient()
    
    # Initialize tools
    history_tool = HistorySearchTool(conversation_repo)
    advice_tool = DailyAdviceTool()

    # Initialize agent
    agent = AIAgent(
        openai_api_key=openai_api_key,
        history_tool=history_tool,
        advice_tool=advice_tool
    )
    
    # Initialize chat service
    chat_service = ChatService(
        user_repository=user_repo,
        conversation_repository=conversation_repo,
        agent=agent
    )
    
    logger.info("Application initialized successfully")
    
    yield
    
    logger.info("Application shutting down...")


# Create FastAPI app
app = FastAPI(
    title="AI Agent Demo",
    description="LangGraph-based AI Agent with tools and memory",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "AI Agent API is running"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Process chat message.
    
    Handles:
    - Normal chat messages
    - Special 'reset context' command
    - Tool invocations via agent
    - Memory persistence
    """
    try:
        logger.info(f"Chat request from user {request.user_id}")
        response = await chat_service.process_message(request)
        return response
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/session/{session_id}")
async def get_session(session_id: str):
    """Get conversation history for a session."""
    try:
        history = await chat_service.get_session_history(session_id)
        return history
    except Exception as e:
        logger.error(f"Get session error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/profile/{user_id}")
async def get_profile(user_id: str):
    """Get user profile."""
    try:
        profile = await user_repo.get_profile(user_id)
        return profile.model_dump(mode='json')
    except Exception as e:
        logger.error(f"Get profile error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/profile/{user_id}")
async def update_profile(user_id: str, request: ProfileUpdateRequest):
    """Update user profile."""
    try:
        updates = request.model_dump(exclude_none=True)
        profile = await user_repo.update_profile(user_id, updates)
        return profile.model_dump(mode='json')
    except Exception as e:
        logger.error(f"Update profile error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/history/search")
async def search_history(q: str):
    """Search across all conversation histories."""
    try:
        results = await chat_service.search_history(q)
        return {"results": results, "count": len(results)}
    except Exception as e:
        logger.error(f"Search history error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
