"""Health check endpoints."""

import logging
from fastapi import APIRouter, status
from pydantic import BaseModel

from ...services import QdrantService, CacheService
from ...config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


class HealthStatus(BaseModel):
    """Health check response model."""

    status: str
    environment: str
    services: dict[str, str]


@router.get("", response_model=HealthStatus, status_code=status.HTTP_200_OK)
async def health_check() -> HealthStatus:
    """Check application health and dependency status.

    Returns:
        Health status including service availability
    """
    services = {}

    # Check Qdrant
    try:
        qdrant_service = QdrantService()
        qdrant_healthy = await qdrant_service.health_check()
        services["qdrant"] = "healthy" if qdrant_healthy else "unhealthy"
        await qdrant_service.close()
    except Exception as e:
        logger.warning(f"Qdrant health check failed: {e}")
        services["qdrant"] = "unhealthy"

    # Check Redis
    try:
        cache_service = CacheService()
        redis_healthy = await cache_service.health_check()
        services["redis"] = "healthy" if redis_healthy else "unhealthy"
        await cache_service.disconnect()
    except Exception as e:
        logger.warning(f"Redis health check failed: {e}")
        services["redis"] = "unhealthy"

    # Overall status
    overall_status = "healthy" if all(
        s == "healthy" for s in services.values()
    ) else "degraded"

    return HealthStatus(
        status=overall_status,
        environment=settings.ENVIRONMENT,
        services=services
    )


@router.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_check() -> dict:
    """Readiness probe for Kubernetes.

    Returns:
        Simple ready status
    """
    return {"ready": True}


@router.get("/live", status_code=status.HTTP_200_OK)
async def liveness_check() -> dict:
    """Liveness probe for Kubernetes.

    Returns:
        Simple alive status
    """
    return {"alive": True}
