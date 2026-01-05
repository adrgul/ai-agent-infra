"""
Logging configuration for the application.

Why this module exists:
- Consistent log format across all modules
- Centralized logging setup prevents duplication
- Structured logging aids debugging and observability

Design decisions:
- Use Python's built-in logging (no external deps for simple demo)
- INFO level default (ERROR/WARNING for production, DEBUG for development)
- Include timestamps and log levels for clarity
"""

import logging
import sys


def setup_logging(level: int = logging.INFO) -> None:
    """
    Configure application-wide logging.

    Why this function: Centralizes logging setup so main.py can initialize once
    and all modules inherit consistent formatting.

    Why stream handler: Logs to stdout for container-friendly operation
    (Docker, Cloud Run, etc. capture stdout).

    Args:
        level: Logging level (default INFO for production readiness)
    """
    # Assert: level must be a valid logging level constant
    assert level in (
        logging.DEBUG,
        logging.INFO,
        logging.WARNING,
        logging.ERROR,
        logging.CRITICAL,
    ), f"Invalid logging level: {level}"

    # Why this format: ISO8601 timestamp, level name, module, and message
    # aids filtering and debugging in production logs
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)  # Container-friendly stdout
        ],
    )

    # Why disable httpx INFO logs: FastAPI/Uvicorn produces verbose HTTP logs
    # that clutter output during normal operation; keep at WARNING
    logging.getLogger("httpx").setLevel(logging.WARNING)

    # Log that logging is configured (useful for confirming setup in container environments)
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured at {logging.getLevelName(level)} level")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.

    Why this function: Provides consistent logger naming pattern and
    ensures all loggers inherit the configured formatting.

    Args:
        name: Logger name (typically __name__ from calling module)

    Returns:
        logging.Logger: Configured logger instance
    """
    # Assert: name should not be empty (logger should have meaningful name)
    assert name.strip(), "Logger name cannot be empty"

    return logging.getLogger(name)
