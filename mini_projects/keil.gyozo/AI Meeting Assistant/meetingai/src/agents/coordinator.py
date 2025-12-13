"""
Coordinator agent for orchestrating meeting processing workflow.

This module contains the CoordinatorAgent class that coordinates
the overall meeting processing pipeline.
"""

import logging
from typing import Dict, Any, Optional, List

from ..utils.config import Config
from ..utils.logger import get_logger
from ..models.meeting import Meeting, MeetingSummary
from ..models.task import TaskList
from .summarizer import SummarizerAgent
from .task_extractor import TaskExtractorAgent

logger = get_logger(__name__)


class CoordinatorAgent:
    """Agent responsible for coordinating the meeting processing workflow."""

    def __init__(self, config: Config):
        """
        Initialize the coordinator agent.

        Args:
            config: Application configuration object
        """
        self.config = config
        self.summarizer = SummarizerAgent(config)
        self.task_extractor = TaskExtractorAgent(config)
        logger.info("CoordinatorAgent initialized successfully")

    async def process_meeting(
        self,
        transcript: str,
        participants: Optional[List[str]] = None,
        title: Optional[str] = None,
        date: Optional[str] = None
    ) -> Meeting:
        """
        Process a complete meeting transcript.

        Args:
            transcript: The meeting transcript text
            participants: List of meeting participants
            title: Meeting title
            date: Meeting date

        Returns:
            Meeting: Complete meeting object with summary and tasks

        Raises:
            RuntimeError: If processing fails
        """
        try:
            logger.info("Starting coordinated meeting processing")

            # Step 1: Generate summary
            logger.info("Step 1: Generating meeting summary")
            summary = await self.summarizer.summarize(transcript, participants)

            # Override title and date if provided
            if title:
                summary.title = title
            if date:
                summary.date = date

            # Step 2: Extract tasks
            logger.info("Step 2: Extracting action items")
            tasks = await self.task_extractor.extract_tasks(
                transcript,
                participants,
                summary.meeting_id
            )

            # Step 3: Create complete meeting object
            meeting = Meeting(
                summary=summary,
                tasks=tasks.tasks
            )

            logger.info("Meeting processing completed successfully")
            return meeting

        except Exception as e:
            logger.error(f"Meeting processing failed: {str(e)}")
            raise RuntimeError(f"Failed to process meeting: {str(e)}")

    async def update_meeting_summary(
        self,
        meeting: Meeting,
        new_transcript: str
    ) -> Meeting:
        """
        Update meeting summary with additional transcript.

        Args:
            meeting: Existing meeting object
            new_transcript: Additional transcript text

        Returns:
            Meeting: Updated meeting object
        """
        try:
            logger.info("Updating meeting summary with additional transcript")

            # Combine transcripts
            combined_transcript = f"{meeting.summary.summary}\n\n{new_transcript}"

            # Re-generate summary
            new_summary = await self.summarizer.summarize(
                combined_transcript,
                meeting.summary.participants
            )

            # Preserve original metadata
            new_summary.meeting_id = meeting.summary.meeting_id
            new_summary.title = meeting.summary.title
            new_summary.date = meeting.summary.date

            # Extract additional tasks
            new_tasks = await self.task_extractor.extract_tasks(
                new_transcript,
                meeting.summary.participants,
                meeting.summary.meeting_id
            )

            # Combine tasks
            all_tasks = meeting.tasks + new_tasks.tasks

            return Meeting(
                summary=new_summary,
                tasks=all_tasks,
                metadata=meeting.metadata
            )

        except Exception as e:
            logger.error(f"Meeting update failed: {str(e)}")
            raise RuntimeError(f"Failed to update meeting: {str(e)}")

    def validate_meeting_data(self, meeting: Meeting) -> bool:
        """
        Validate meeting data completeness.

        Args:
            meeting: Meeting object to validate

        Returns:
            True if valid
        """
        if not meeting.summary.summary.strip():
            logger.warning("Meeting summary is empty")
            return False

        if not meeting.summary.participants:
            logger.warning("No participants specified")
            return False

        if not meeting.summary.meeting_id:
            logger.warning("Missing meeting ID")
            return False

        return True