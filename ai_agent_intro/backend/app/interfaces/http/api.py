"""FastAPI HTTP API routes."""
from datetime import date
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from loguru import logger

from app.domain.models import BriefingResponse, HistoryEntry, UserProfile
from app.interfaces.container import Container


def create_router(container: Container) -> APIRouter:
    """
    Create FastAPI router with dependency injection.

    Args:
        container: DI container

    Returns:
        Configured API router
    """
    router = APIRouter(prefix="/api")

    @router.get("/briefing", response_model=BriefingResponse)
    async def get_briefing(
        city: Annotated[str, Query(description="City name", min_length=1)],
        target_date: Annotated[
            date | None,
            Query(
                alias="date",
                description="Target date in ISO-8601 format (YYYY-MM-DD)",
            ),
        ] = None,
        language: Annotated[
            str | None,
            Query(
                description="Language code for the response (e.g., 'en', 'es', 'fr')",
                min_length=2,
                max_length=5,
            ),
        ] = None,
    ) -> BriefingResponse:
        """
        Get weather briefing for a city and date.

        Args:
            city: City name to get weather for
            target_date: Target date (defaults to today)
            language: Language code for the response (defaults to English)

        Returns:
            Weather briefing with outfit and activity suggestions

        Raises:
            HTTPException: If request fails
        """
        if target_date is None:
            target_date = date.today()

        logger.info(f"Briefing request: {city} on {target_date} (language: {language or 'en'})")

        try:
            result = await container.briefing_usecase.execute(city, target_date, language)
            logger.info(f"Briefing completed successfully for {city}")
            return result

        except ValueError as e:
            logger.warning(f"Validation error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Briefing failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate briefing: {str(e)}",
            )

    @router.get("/history", response_model=list[HistoryEntry])
    async def get_history(
        limit: Annotated[int, Query(description="Maximum entries", ge=1, le=100)] = 20,
    ) -> list[HistoryEntry]:
        """
        Get recent briefing request history.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of recent history entries
        """
        logger.info(f"History request: limit={limit}")

        try:
            history = await container.history_repository.get_recent(limit)
            logger.info(f"Returned {len(history)} history entries")
            return history

        except Exception as e:
            logger.error(f"Failed to fetch history: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch history: {str(e)}",
            )

    @router.get("/profile", response_model=UserProfile | None)
    async def get_profile() -> UserProfile | None:
        """
        Get user profile.

        Returns:
            User profile if exists, None otherwise
        """
        logger.info("Profile GET request")

        try:
            profile = await container.profile_repository.get_profile()
            if profile:
                logger.info("Profile found")
            else:
                logger.info("No profile exists")
            return profile

        except Exception as e:
            logger.error(f"Failed to fetch profile: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch profile: {str(e)}",
            )

    @router.put("/profile", response_model=UserProfile)
    async def update_profile(profile: UserProfile) -> UserProfile:
        """
        Update user profile.

        Args:
            profile: User profile to save

        Returns:
            Saved user profile
        """
        logger.info(f"Profile PUT request: {profile.model_dump()}")

        try:
            await container.profile_repository.save_profile(profile)
            logger.info("Profile saved successfully")
            return profile

        except Exception as e:
            logger.error(f"Failed to save profile: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save profile: {str(e)}",
            )

    return router
