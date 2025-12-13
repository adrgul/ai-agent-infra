"""
External API integrations for MeetingAI
"""

from .jira_client import JiraClient
from .calendar_client import CalendarClient
from .email_client import EmailClient
from .slack_client import SlackClient

__all__ = [
    "JiraClient",
    "CalendarClient",
    "EmailClient",
    "SlackClient"
]