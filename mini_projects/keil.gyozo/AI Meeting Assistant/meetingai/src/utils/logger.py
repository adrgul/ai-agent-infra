"""
Logging setup for MeetingAI
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional

import colorlog

from .config import Config


def setup_logger(
    name: str = "meetingai",
    config: Optional[Config] = None,
    level: Optional[str] = None,
    file_path: Optional[str] = None
) -> logging.Logger:
    """
    Setup logger with console and file handlers

    Args:
        name: Logger name
        config: Configuration object
        level: Log level override
        file_path: Log file path override

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # Set to DEBUG, handlers will filter

    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Determine log level
    log_level = level or (config.logging.level if config else "INFO")
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Console handler with colors
    console_handler = colorlog.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler (if configured)
    log_file = file_path or (config.logging.file if config else None)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=config.logging.max_bytes if config else 10485760,
            backupCount=config.logging.backup_count if config else 5
        )
        file_handler.setLevel(numeric_level)

        file_formatter = logging.Formatter(
            config.logging.format if config else "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get logger instance

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


# Global logger instance
logger = setup_logger()