"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .utils.logging import setup_logging
from .api.routes import health, tickets
from .api.middleware.logging import LoggingMiddleware
from .api.middleware.error_handler import ErrorHandlerMiddleware

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info(f"Starting {settings.APP_NAME} - Environment: {settings.ENVIRONMENT}")

    # Initialize workflow
    tickets.initialize_workflow()

    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info("Application shutting down")

    # Cleanup resources
    if tickets.qdrant_service:
        await tickets.qdrant_service.close()

    logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="SupportAI",
    description=(
        "AI-powered customer support triage and response generation system. "
        "Automatically classifies tickets, assigns priority, and generates "
        "draft responses with knowledge base citations."
    ),
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(LoggingMiddleware)

# Include routers
app.include_router(health.router)
app.include_router(tickets.router)


@app.get("/", tags=["root"])
async def root() -> dict:
    """Root endpoint.

    Returns:
        Welcome message and API info
    """
    return {
        "name": settings.APP_NAME,
        "version": "0.1.0",
        "environment": settings.ENVIRONMENT,
        "docs": "/docs" if settings.ENVIRONMENT != "production" else None
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
