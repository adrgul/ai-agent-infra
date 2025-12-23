"""
FastAPI application entry point.

Why this module exists:
- Main application factory and configuration
- Registers all API routers
- Configures middleware, CORS, and logging
- Entry point for uvicorn server

Design decisions:
- Lifespan context manager for startup/shutdown tasks
- CORS enabled for Streamlit frontend (separate origin in deployment)
- Logging configured at startup
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import chat, health, ingest
from app.core.config import get_settings
from app.core.logging import get_logger, setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown tasks.

    Why this exists: FastAPI's recommended way to run code at startup/shutdown.
    Replaces deprecated @app.on_event decorators.

    Why we need it:
    - Configure logging once at startup
    - (Future) Pre-load models or connect to external services
    - Clean shutdown of resources

    Args:
        app: FastAPI application instance
    """
    # Assert: app must be a FastAPI instance
    assert isinstance(app, FastAPI), "Lifespan requires FastAPI app instance"

    # Startup: Configure logging
    setup_logging()
    logger = get_logger(__name__)

    settings = get_settings()
    logger.info("Starting FastAPI application")
    logger.info(f"DOCS_PATH: {settings.DOCS_PATH}")
    logger.info(f"VECTORSTORE_DIR: {settings.VECTORSTORE_DIR}")
    logger.info(f"Chat model: {settings.OPENAI_CHAT_MODEL}")
    logger.info(f"Embed model: {settings.OPENAI_EMBED_MODEL}")

    # Why log LangSmith status: Confirms observability setup for debugging
    if settings.LANGSMITH_TRACING:
        logger.info(f"LangSmith tracing enabled (project: {settings.LANGSMITH_PROJECT})")
        # Set environment variables for LangChain to pick up
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = settings.LANGSMITH_API_KEY or ""
        os.environ["LANGCHAIN_PROJECT"] = settings.LANGSMITH_PROJECT
    else:
        logger.info("LangSmith tracing disabled")

    yield  # Application runs here

    # Shutdown: Clean up resources
    logger.info("Shutting down FastAPI application")


# Why title/version: Appears in OpenAPI docs for identification
app = FastAPI(
    title="Streamlit FastAPI FAISS RAG Demo",
    version="0.1.0",
    description="Demo RAG chatbot backend with FAISS vector store",
    lifespan=lifespan,
)

# Why CORS: Streamlit frontend runs on different origin (localhost:8501 or deployed URL)
# Must allow cross-origin requests for API calls to succeed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production: specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
# Why separate routers: Modular organization; each router handles related endpoints
app.include_router(health.router, tags=["Health"])
app.include_router(ingest.router, tags=["Ingestion"])
app.include_router(chat.router, tags=["Chat"])


@app.get("/")
async def root():
    """
    Root endpoint redirect.

    Why this exists: Provides helpful message when accessing API root.
    Points users to interactive documentation.
    """
    return {
        "message": "FastAPI RAG Backend",
        "docs": "/docs",
        "openapi": "/openapi.json",
    }
