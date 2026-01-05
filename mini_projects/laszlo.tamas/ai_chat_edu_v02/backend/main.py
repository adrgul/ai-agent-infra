import logging
import os
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from api.routes import router
from api.document_endpoints import router as document_router
from api.session_endpoints import router as session_router
from api.websocket_endpoints import router as websocket_router
from api.admin_endpoints import router as admin_router
from database.pg_init import init_postgres_schema

# Configure logging
import sys
log_level = os.getenv("LOG_LEVEL", "INFO").upper()

# Force UTF-8 for stdout/stderr (Windows compatibility)
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

logging.basicConfig(
    level=getattr(logging, log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    logger.info("Starting application...")
    # Initialize PostgreSQL schema
    init_postgres_schema()
    logger.info("PostgreSQL schema initialized")
    yield
    logger.info("Shutting down application...")


# Load version from system.ini
def get_app_version() -> str:
    """Read APP_VERSION from system.ini."""
    try:
        from config.config_service import get_config_value
        return get_config_value("application", "APP_VERSION", "0.0.0")
    except Exception as e:
        logger.warning(f"Failed to load APP_VERSION from system.ini: {e}")
        return "0.0.0"

APP_VERSION = get_app_version()

app = FastAPI(
    title=f"AI Chat {APP_VERSION}",
    description="Multi-tenant chat with LangGraph, RAG, and LTM",
    version=APP_VERSION,
    lifespan=lifespan,
    default_response_class=ORJSONResponse  # Use ORJSON for proper UTF-8 handling
)

# Configure CORS - Local development only
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api")
app.include_router(document_router)  # Already has /api/documents prefix
app.include_router(session_router)  # Already has /api/sessions prefix
app.include_router(admin_router)  # Already has /api/admin prefix
app.include_router(websocket_router)  # WebSocket endpoints (no prefix)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "message": f"AI Chat {APP_VERSION} API", "version": APP_VERSION}


@app.get("/api/version")
async def get_version():
    """Get application version."""
    return {"version": APP_VERSION, "name": f"AI Chat {APP_VERSION}"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}
