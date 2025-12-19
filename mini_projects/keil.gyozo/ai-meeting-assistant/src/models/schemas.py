"""
Pydantic models for the AI Meeting Assistant.

This module defines the data structures for meeting transcripts,
action items, summaries, and the final processed output.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


class ActionItem(BaseModel):
    """Represents a single action item extracted from a meeting."""

    task: str = Field(
        ...,
        description="Description of the action item/task to be completed"
    )
    assignee: Optional[str] = Field(
        None,
        description="Person assigned to complete this task"
    )
    deadline: Optional[str] = Field(
        None,
        description="Deadline for completing the task (if mentioned)"
    )
    priority: Optional[str] = Field(
        None,
        description="Priority level: high, medium, or low"
    )

    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v: Optional[str]) -> Optional[str]:
        """Validate that priority is one of the allowed values."""
        if v is not None:
            allowed = ['high', 'medium', 'low']
            v_lower = v.lower()
            if v_lower not in allowed:
                return 'medium'  # Default to medium if invalid
            return v_lower
        return v


class MeetingSummary(BaseModel):
    """Represents the executive summary of a meeting."""

    summary: str = Field(
        ...,
        description="Concise executive summary of the meeting (2-4 sentences)"
    )
    key_points: List[str] = Field(
        default_factory=list,
        description="List of key discussion points and decisions"
    )
    participants: Optional[List[str]] = Field(
        None,
        description="List of meeting participants (if identifiable)"
    )
    meeting_date: Optional[str] = Field(
        None,
        description="Date of the meeting (if mentioned)"
    )


class MeetingTranscript(BaseModel):
    """Input model for raw meeting transcript."""

    transcript: str = Field(
        ...,
        description="Raw text of the meeting transcript"
    )
    metadata: Optional[dict] = Field(
        default_factory=dict,
        description="Optional metadata about the meeting"
    )


class ProcessedMeeting(BaseModel):
    """Complete output model containing all processed meeting information."""

    summary: MeetingSummary = Field(
        ...,
        description="Executive summary of the meeting"
    )
    action_items: List[ActionItem] = Field(
        default_factory=list,
        description="List of extracted action items"
    )
    processed_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp when the meeting was processed"
    )

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class GraphState(BaseModel):
    """State object that flows through the LangGraph workflow."""

    # Input
    transcript: str = Field(
        ...,
        description="Raw meeting transcript text"
    )

    # Intermediate results
    parsed_transcript: Optional[str] = Field(
        None,
        description="Cleaned/parsed transcript"
    )

    # Outputs
    summary: Optional[MeetingSummary] = Field(
        None,
        description="Generated meeting summary"
    )
    action_items: Optional[List[ActionItem]] = Field(
        None,
        description="Extracted action items"
    )

    # Processing metadata
    errors: List[str] = Field(
        default_factory=list,
        description="Any errors encountered during processing"
    )

    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True
