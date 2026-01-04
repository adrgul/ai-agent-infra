"""
Health check endpoint for service monitoring.

Why this module exists:
- Provides a simple health check for load balancers and monitoring tools
- Confirms the service is running and responding to HTTP requests
- No dependencies on external services (fast response)

Design decisions:
- No authentication required (health checks should always succeed if service is up)
- Always returns 200 OK (more sophisticated health checks can be added later)
"""

from fastapi import APIRouter

from app.core.logging import get_logger
from app.schemas.common import HealthResponse

# Why separate router: Modular design allows mounting health endpoint
# independently from other API routes (e.g., at /health or /_health)
router = APIRouter()

logger = get_logger(__name__)


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Why this endpoint: Load balancers (Cloud Run, Kubernetes, etc.) need
    a simple endpoint to verify service is running.

    Why async: FastAPI supports async handlers; even though this is synchronous
    work, using async is idiomatic and allows proper concurrency handling.

    Returns:
        HealthResponse: Status indicating service is healthy
    """
    # Assert: This function must always return a valid HealthResponse
    # (If this function executes, the service is by definition healthy)

    logger.debug("Health check called")

    return HealthResponse(status="ok")
