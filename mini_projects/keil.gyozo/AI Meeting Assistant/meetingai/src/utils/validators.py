"""
Validation utilities for MeetingAI
"""

import os
from pathlib import Path
from typing import List

from .config import Config


def validate_file_format(file_path: str, config: Config) -> bool:
    """
    Validate file format is supported

    Args:
        file_path: Path to the file
        config: Configuration object

    Returns:
        True if valid

    Raises:
        ValueError: If format is not supported
    """
    path = Path(file_path)
    extension = path.suffix.lower().lstrip('.')

    if extension not in config.input.supported_formats:
        raise ValueError(
            f"Unsupported file format: {extension}. "
            f"Supported formats: {config.input.supported_formats}"
        )

    return True


def validate_file_size(file_path: str, config: Config) -> bool:
    """
    Validate file size is within limits

    Args:
        file_path: Path to the file
        config: Configuration object

    Returns:
        True if valid

    Raises:
        ValueError: If file is too large
    """
    max_size_bytes = config.input.max_file_size_mb * 1024 * 1024
    file_size = os.path.getsize(file_path)

    if file_size > max_size_bytes:
        raise ValueError(
            f"File too large: {file_size / (1024*1024):.1f}MB. "
            f"Maximum size: {config.input.max_file_size_mb}MB"
        )

    return True


def validate_file_exists(file_path: str) -> bool:
    """
    Validate file exists

    Args:
        file_path: Path to the file

    Returns:
        True if exists

    Raises:
        FileNotFoundError: If file doesn't exist
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    return True


def validate_directory_exists(dir_path: str) -> bool:
    """
    Validate directory exists, create if not

    Args:
        dir_path: Path to the directory

    Returns:
        True if exists or created
    """
    path = Path(dir_path)
    path.mkdir(parents=True, exist_ok=True)
    return True


def validate_meeting_participants(participants: List[str]) -> bool:
    """
    Validate meeting participants list

    Args:
        participants: List of participant names

    Returns:
        True if valid

    Raises:
        ValueError: If participants list is invalid
    """
    if not participants:
        raise ValueError("At least one participant is required")

    if len(participants) > 50:
        raise ValueError("Too many participants (max 50)")

    for participant in participants:
        if not participant.strip():
            raise ValueError("Participant names cannot be empty")
        if len(participant) > 100:
            raise ValueError("Participant name too long (max 100 characters)")

    return True


def validate_task_assignee(assignee: str) -> bool:
    """
    Validate task assignee

    Args:
        assignee: Assignee name

    Returns:
        True if valid

    Raises:
        ValueError: If assignee is invalid
    """
    if not assignee or not assignee.strip():
        raise ValueError("Assignee cannot be empty")

    if len(assignee) > 100:
        raise ValueError("Assignee name too long (max 100 characters)")

    return True