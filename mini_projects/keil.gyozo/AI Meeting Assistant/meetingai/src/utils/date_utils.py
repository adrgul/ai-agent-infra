"""
Date and time utilities for MeetingAI
"""

from datetime import datetime, date
from typing import Optional


def parse_date(date_str: str) -> Optional[date]:
    """
    Parse date string in various formats

    Args:
        date_str: Date string to parse

    Returns:
        Parsed date object or None if invalid
    """
    formats = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%Y/%m/%d",
        "%d-%m-%Y",
        "%m-%d-%Y",
        "%B %d, %Y",
        "%d %B %Y",
        "%Y%m%d"
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue

    return None


def format_date(date_obj: date, format_str: str = "%Y-%m-%d") -> str:
    """
    Format date object to string

    Args:
        date_obj: Date object to format
        format_str: Format string

    Returns:
        Formatted date string
    """
    return date_obj.strftime(format_str)


def get_current_date(format_str: str = "%Y-%m-%d") -> str:
    """
    Get current date as formatted string

    Args:
        format_str: Format string

    Returns:
        Current date string
    """
    return datetime.now().strftime(format_str)


def get_current_datetime(format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Get current datetime as formatted string

    Args:
        format_str: Format string

    Returns:
        Current datetime string
    """
    return datetime.now().strftime(format_str)


def calculate_due_date_from_text(text: str) -> Optional[str]:
    """
    Extract due date from text using simple heuristics

    Args:
        text: Text to parse

    Returns:
        Due date string (YYYY-MM-DD) or None
    """
    import re
    from datetime import timedelta

    text_lower = text.lower()

    # Look for relative dates
    if "tomorrow" in text_lower:
        due_date = date.today() + timedelta(days=1)
        return format_date(due_date)
    elif "next week" in text_lower:
        due_date = date.today() + timedelta(weeks=1)
        return format_date(due_date)
    elif "end of week" in text_lower or "eow" in text_lower:
        today = date.today()
        days_until_friday = (4 - today.weekday()) % 7
        if days_until_friday == 0:
            days_until_friday = 7
        due_date = today + timedelta(days=days_until_friday)
        return format_date(due_date)
    elif "end of month" in text_lower or "eom" in text_lower:
        today = date.today()
        if today.month == 12:
            due_date = date(today.year + 1, 1, 1) - timedelta(days=1)
        else:
            due_date = date(today.year, today.month + 1, 1) - timedelta(days=1)
        return format_date(due_date)

    # Look for specific dates
    date_patterns = [
        r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})",  # DD/MM/YYYY or MM/DD/YYYY
        r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})",  # YYYY/MM/DD
        r"(\w{3,})\s+(\d{1,2}),?\s+(\d{4})",   # Month DD, YYYY
        r"(\d{1,2})\s+(\w{3,})\s+(\d{4})",     # DD Month YYYY
    ]

    for pattern in date_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            try:
                if len(match) == 3:
                    parsed = parse_date(" ".join(match))
                    if parsed:
                        return format_date(parsed)
            except:
                continue

    return None


def is_overdue(due_date_str: str) -> bool:
    """
    Check if a due date is overdue

    Args:
        due_date_str: Due date string (YYYY-MM-DD)

    Returns:
        True if overdue
    """
    try:
        due_date = datetime.fromisoformat(due_date_str).date()
        return due_date < date.today()
    except (ValueError, TypeError):
        return False