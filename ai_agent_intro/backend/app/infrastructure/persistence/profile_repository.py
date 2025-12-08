"""User profile repository implementation."""
import json
from pathlib import Path
from typing import Optional

from loguru import logger

from app.domain.models import UserProfile


class FileUserProfileRepository:
    """File-based user profile repository using JSON."""

    def __init__(self, data_dir: str):
        """
        Initialize file-based profile repository.

        Args:
            data_dir: Directory to store profile file
        """
        self.data_dir = Path(data_dir)
        self.profile_file = self.data_dir / "user_profile.json"

        # Ensure data directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)

    async def get_profile(self) -> Optional[UserProfile]:
        """
        Get the user profile.

        Returns:
            User profile if exists, None otherwise
        """
        try:
            if not self.profile_file.exists():
                logger.debug("No user profile found")
                return None

            with open(self.profile_file, "r") as f:
                data = json.load(f)

            profile = UserProfile(**data)
            logger.info("User profile loaded successfully")
            return profile

        except Exception as e:
            logger.error(f"Failed to load user profile: {e}")
            return None

    async def save_profile(self, profile: UserProfile) -> None:
        """
        Save or update the user profile.

        Args:
            profile: User profile to save
        """
        try:
            # Write to temp file first for atomicity
            temp_file = self.profile_file.with_suffix(".tmp")

            with open(temp_file, "w") as f:
                json.dump(profile.model_dump(), f, indent=2)

            # Atomic rename
            temp_file.replace(self.profile_file)

            logger.info("User profile saved successfully")

        except Exception as e:
            logger.error(f"Failed to save user profile: {e}")
            raise
