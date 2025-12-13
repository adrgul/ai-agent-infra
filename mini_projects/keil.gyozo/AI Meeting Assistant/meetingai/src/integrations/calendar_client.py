"""
Calendar integration client (Google Calendar / Outlook)
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from ..utils.config import Config
from ..utils.logger import get_logger

logger = get_logger(__name__)


class CalendarClient:
    """Client for calendar integrations (Google Calendar, Outlook)"""

    def __init__(self, config: Config):
        """
        Initialize calendar client

        Args:
            config: Application configuration
        """
        self.config = config
        self.provider = config.integrations.calendar.provider
        self.service = None

        if config.integrations.calendar.enabled:
            self._setup_service()

    def _setup_service(self):
        """Setup calendar service based on provider"""
        if self.provider == "google":
            self._setup_google_calendar()
        elif self.provider == "outlook":
            self._setup_outlook_calendar()
        else:
            raise ValueError(f"Unsupported calendar provider: {self.provider}")

    def _setup_google_calendar(self):
        """Setup Google Calendar API"""
        try:
            from googleapiclient.discovery import build
            from google.oauth2.credentials import Credentials

            # This would require proper OAuth flow in production
            # For now, assume credentials are available
            creds = None  # Load from file/token
            self.service = build('calendar', 'v3', credentials=creds)

        except ImportError:
            logger.warning("Google Calendar dependencies not installed")
        except Exception as e:
            logger.error(f"Failed to setup Google Calendar: {str(e)}")

    def _setup_outlook_calendar(self):
        """Setup Outlook/Microsoft Graph API"""
        try:
            # Microsoft Graph API setup would go here
            self.service = None  # Placeholder

        except Exception as e:
            logger.error(f"Failed to setup Outlook Calendar: {str(e)}")

    async def create_event(
        self,
        title: str,
        description: str,
        start_time: datetime,
        attendees: List[str] = None,
        duration_minutes: int = None
    ) -> Optional[str]:
        """
        Create a calendar event

        Args:
            title: Event title
            description: Event description
            start_time: Event start time
            attendees: List of attendee email addresses
            duration_minutes: Event duration in minutes

        Returns:
            Event ID if successful
        """
        if not self.config.integrations.calendar.enabled or not self.service:
            logger.info("Calendar integration disabled or not configured")
            return None

        try:
            duration = duration_minutes or self.config.integrations.calendar.default_duration_minutes
            end_time = start_time + timedelta(minutes=duration)

            event_data = {
                'summary': title,
                'description': description,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'UTC',
                },
            }

            if attendees:
                event_data['attendees'] = [{'email': email} for email in attendees]

            # Add reminder
            reminder_minutes = self.config.integrations.calendar.default_reminder_minutes
            event_data['reminders'] = {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': reminder_minutes},
                    {'method': 'popup', 'minutes': reminder_minutes},
                ],
            }

            if self.provider == "google":
                event = self.service.events().insert(
                    calendarId='primary',
                    body=event_data
                ).execute()
                event_id = event.get('id')
                logger.info(f"Created Google Calendar event: {event_id}")
                return event_id

            # Outlook implementation would go here

        except Exception as e:
            logger.error(f"Error creating calendar event: {str(e)}")
            return None

    async def create_followup_meeting(
        self,
        meeting_title: str,
        participants: List[str],
        suggested_date: datetime = None
    ) -> Optional[str]:
        """
        Create a follow-up meeting event

        Args:
            meeting_title: Title of the original meeting
            participants: List of participant email addresses
            suggested_date: Suggested date for follow-up

        Returns:
            Event ID if successful
        """
        title = f"Follow-up: {meeting_title}"
        description = f"Follow-up meeting for: {meeting_title}"

        # Use suggested date or next week
        start_time = suggested_date or (datetime.now() + timedelta(days=7))

        return await self.create_event(
            title=title,
            description=description,
            start_time=start_time,
            attendees=participants
        )