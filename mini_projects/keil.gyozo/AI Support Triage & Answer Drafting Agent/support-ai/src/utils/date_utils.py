"""
Date and time utilities for SupportAI.

Parsing, formatting, and timezone handling.
"""

import re
from datetime import datetime, timedelta
from typing import Optional, Tuple

from .logger import get_logger

logger = get_logger(__name__)


def parse_date_from_text(text: str) -> Optional[datetime]:
    """
    Extract and parse dates from natural language text.

    Args:
        text: Text containing date references

    Returns:
        Parsed datetime or None if no date found
    """
    # Common date patterns
    patterns = [
        # MM/DD/YYYY
        r'(\d{1,2})/(\d{1,2})/(\d{4})',
        # DD/MM/YYYY
        r'(\d{1,2})\.(\d{1,2})\.(\d{4})',
        # YYYY-MM-DD
        r'(\d{4})-(\d{2})-(\d{2})',
        # Month DD, YYYY
        r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})',
        # DD Month YYYY
        r'(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})'
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                if len(match.groups()) == 3:
                    # Numeric date
                    parts = [int(g) for g in match.groups()]
                    if len(parts) == 3:
                        # Assume MM/DD/YYYY or DD/MM/YYYY - try both
                        try:
                            return datetime(parts[2], parts[0], parts[1])
                        except ValueError:
                            try:
                                return datetime(parts[2], parts[1], parts[0])
                            except ValueError:
                                continue
                else:
                    # Month name date
                    month_name, day, year = match.groups()
                    month_names = {
                        'january': 1, 'february': 2, 'march': 3, 'april': 4,
                        'may': 5, 'june': 6, 'july': 7, 'august': 8,
                        'september': 9, 'october': 10, 'november': 11, 'december': 12
                    }
                    month = month_names.get(month_name.lower())
                    if month:
                        return datetime(int(year), month, int(day))
            except (ValueError, IndexError) as e:
                logger.debug(f"Failed to parse date from {match.groups()}: {e}")
                continue

    return None


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def calculate_sla_deadline(priority: str, sla_hours: int) -> datetime:
    """
    Calculate SLA deadline from current time.

    Args:
        priority: Priority level (P1, P2, P3)
        sla_hours: SLA time in hours

    Returns:
        Deadline datetime
    """
    # Business hours calculation could be added here
    # For now, simple addition
    return datetime.utcnow() + timedelta(hours=sla_hours)


def get_business_hours_delay(start_time: datetime, hours: int) -> datetime:
    """
    Calculate deadline considering business hours (9-5, Mon-Fri).

    Args:
        start_time: Start datetime
        hours: Business hours to add

    Returns:
        End datetime
    """
    # Simplified implementation - could be enhanced
    # For now, just add the hours
    return start_time + timedelta(hours=hours)


def format_datetime_for_display(dt: datetime) -> str:
    """
    Format datetime for user display.

    Args:
        dt: Datetime to format

    Returns:
        Formatted string
    """
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")