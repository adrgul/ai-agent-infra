import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router
from database.db import init_database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    logger.info("Starting application...")
    init_database()
    logger.info("Database initialized")
    yield
    logger.info("Shutting down application...")


app = FastAPI(
    title="AI Chat Phase 1",
    description="Multi-user chat engine with OpenAI integration",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "AI Chat Phase 1 API"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}
