"""Logging utilities."""
import sys

from loguru import logger

from app.config.settings import Settings


def setup_logging(settings: Settings) -> None:
    """
    Configure logging for the application.

    Args:
        settings: Application settings
    """
    # Remove default handler
    logger.remove()

    # Add custom handler with formatting
    logger.add(
        sys.stderr,
        level=settings.log_level,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        ),
        colorize=True,
    )

    # Filter out sensitive information
    logger.add(
        lambda msg: "api_key" not in msg.lower() and "apikey" not in msg.lower(),
        level="WARNING",
    )

    logger.info(f"Logging configured at {settings.log_level} level")
