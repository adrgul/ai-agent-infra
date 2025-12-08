"""Main FastAPI application."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config.settings import get_settings
from app.interfaces.container import create_container
from app.interfaces.http.api import create_router
from app.utils.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    settings = get_settings()
    
    # Setup logging
    setup_logging(settings)
    logger.info("Starting AI Weather Agent backend")
    
    # Ensure data directory exists
    settings.ensure_data_dir()
    logger.info(f"Data directory: {settings.data_dir}")
    
    yield
    
    logger.info("Shutting down AI Weather Agent backend")


# Create FastAPI app
app = FastAPI(
    title="AI Weather Agent API",
    description="AI-powered weather briefing service with outfit and activity suggestions",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create container and router
settings = get_settings()
container = create_container(settings, use_langgraph=settings.use_langgraph)
api_router = create_router(container)

# Include router
app.include_router(api_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=settings.port)
