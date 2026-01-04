"""
API Tools for the LangChain agent.

APIs used:
- ip-api.com: IP geolocation, timezone
- Nager.Date API: Public holidays
"""

from datetime import datetime, timedelta
from typing import Optional
import requests
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from config import get_settings


class LocationInfo(BaseModel):
    """IP-based location information."""
    ip: str
    country: str
    country_code: str
    city: str
    timezone: str
    isp: Optional[str] = None


class Holiday(BaseModel):
    """Public holiday."""
    date: str
    name: str
    local_name: str


@tool
def get_location_info(ip_address: str) -> dict:
    """
    Get location information for an IP address using ip-api.com.
    Returns country, city, timezone, and country code.

    Args:
        ip_address: The IP address to look up (e.g., "8.8.8.8")

    Returns:
        Dictionary with location info: country, city, timezone, country_code
    """
    settings = get_settings()

    try:
        url = f"{settings.ip_api_url}/{ip_address}?lang=hu"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "fail":
            return {
                "error": True,
                "message": f"Failed to query IP address: {data.get('message', 'Unknown error')}"
            }

        return {
            "error": False,
            "ip": ip_address,
            "country": data.get("country", "Unknown"),
            "country_code": data.get("countryCode", ""),
            "city": data.get("city", "Unknown"),
            "region": data.get("regionName", ""),
            "timezone": data.get("timezone", "UTC"),
            "isp": data.get("isp", ""),
        }
    except requests.RequestException as e:
        return {
            "error": True,
            "message": f"Network error: {str(e)}"
        }


@tool
def get_holidays(country_code: str, year: Optional[int] = None) -> dict:
    """
    Get public holidays for a country using Nager.Date API.

    Args:
        country_code: Two-letter country code (e.g., "HU", "DE", "US")
        year: Year to get holidays for (defaults to current year)

    Returns:
        Dictionary with list of holidays for the country
    """
    settings = get_settings()

    if year is None:
        year = datetime.now().year

    try:
        url = f"{settings.holidays_api_url}/{year}/{country_code}"
        response = requests.get(url, timeout=10)

        if response.status_code == 404:
            return {
                "error": False,
                "country_code": country_code,
                "year": year,
                "holidays": [],
                "message": "No data available for this country"
            }

        response.raise_for_status()
        data = response.json()

        holidays = []
        for h in data:
            holidays.append({
                "date": h.get("date"),
                "name": h.get("name"),
                "local_name": h.get("localName", h.get("name")),
            })

        return {
            "error": False,
            "country_code": country_code,
            "year": year,
            "holidays": holidays,
        }
    except requests.RequestException as e:
        return {
            "error": True,
            "message": f"Network error: {str(e)}"
        }


@tool
def calculate_sla_deadline(
    timezone: str,
    priority: str,
    country_code: str = ""
) -> dict:
    """
    Calculate SLA deadline based on priority and timezone.
    Takes into account business hours (9:00-18:00) and holidays.

    Args:
        timezone: Customer's timezone (e.g., "Europe/Budapest", "America/New_York")
        priority: Priority level ("P1", "P2", "P3", "P4")
        country_code: Two-letter country code for holiday checking (optional)

    Returns:
        Dictionary with SLA deadline information
    """
    # SLA response times by priority (in hours)
    sla_hours = {
        "P1": 4,    # Critical - 4 hours
        "P2": 8,    # High - 8 hours (1 business day)
        "P3": 24,   # Medium - 24 hours
        "P4": 72,   # Low - 72 hours (3 business days)
    }

    priority_names = {
        "P1": "Critical",
        "P2": "High",
        "P3": "Medium",
        "P4": "Low",
    }

    hours = sla_hours.get(priority.upper(), 24)
    priority_name = priority_names.get(priority.upper(), "Unknown")

    # Current time
    now = datetime.now()
    deadline = now + timedelta(hours=hours)

    # Check for holidays (if country code provided)
    holidays_in_range = []
    if country_code:
        try:
            holidays_result = get_holidays.invoke({
                "country_code": country_code,
                "year": now.year
            })
            if not holidays_result.get("error"):
                for h in holidays_result.get("holidays", []):
                    holiday_date = datetime.strptime(h["date"], "%Y-%m-%d").date()
                    if now.date() <= holiday_date <= deadline.date():
                        holidays_in_range.append(h)
                        # If a holiday falls within the range, add 24 hours
                        deadline += timedelta(hours=24)
        except Exception:
            pass  # If query fails, continue without it

    return {
        "priority": priority.upper(),
        "priority_name": priority_name,
        "sla_hours": hours,
        "deadline": deadline.strftime("%Y-%m-%d %H:%M"),
        "deadline_local_format": deadline.strftime("%Y. %m. %d. %H:%M"),
        "timezone": timezone,
        "holidays_affecting": holidays_in_range,
        "adjusted_for_holidays": len(holidays_in_range) > 0,
    }


# Tool list for the agent
TOOLS = [get_location_info, get_holidays, calculate_sla_deadline]
