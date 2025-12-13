"""
JSON schemas for validation
"""

from typing import Any, Dict

# Meeting Summary JSON Schema
MEETING_SUMMARY_SCHEMA = {
    "type": "object",
    "properties": {
        "meeting_id": {"type": "string"},
        "title": {"type": "string"},
        "date": {"type": "string", "format": "date"},
        "participants": {
            "type": "array",
            "items": {"type": "string"}
        },
        "summary": {"type": "string"},
        "key_decisions": {
            "type": "array",
            "items": {"type": "string"}
        },
        "next_steps": {
            "type": "array",
            "items": {"type": "string"}
        }
    },
    "required": ["meeting_id", "title", "date", "summary"]
}

# Task JSON Schema
TASK_SCHEMA = {
    "type": "object",
    "properties": {
        "task_id": {"type": "string"},
        "title": {"type": "string"},
        "assignee": {"type": "string"},
        "due_date": {"type": "string", "format": "date"},
        "priority": {"type": "string", "enum": ["Low", "Medium", "High", "P1", "P2", "P3"]},
        "status": {"type": "string", "enum": ["to-do", "in-progress", "done", "cancelled"]},
        "meeting_reference": {"type": "string"},
        "description": {"type": "string"}
    },
    "required": ["task_id", "title", "assignee", "meeting_reference"]
}

# Complete Meeting JSON Schema
MEETING_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": MEETING_SUMMARY_SCHEMA,
        "tasks": {
            "type": "array",
            "items": TASK_SCHEMA
        },
        "metadata": {"type": "object"},
        "processed_at": {"type": "string", "format": "date-time"}
    },
    "required": ["summary"]
}

def validate_meeting_data(data: Dict[str, Any]) -> bool:
    """
    Validate meeting data against schema

    Args:
        data: Meeting data dictionary

    Returns:
        True if valid, raises exception if invalid
    """
    from pydantic import ValidationError
    from .meeting import Meeting

    try:
        Meeting(**data)
        return True
    except ValidationError as e:
        raise ValueError(f"Invalid meeting data: {e}")

def validate_task_data(data: Dict[str, Any]) -> bool:
    """
    Validate task data against schema

    Args:
        data: Task data dictionary

    Returns:
        True if valid, raises exception if invalid
    """
    from pydantic import ValidationError
    from .task import Task

    try:
        Task(**data)
        return True
    except ValidationError as e:
        raise ValueError(f"Invalid task data: {e}")