"""
Meeting data models using Pydantic
"""

from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, validator


class MeetingSummary(BaseModel):
    """Model for meeting summary data"""

    meeting_id: str = Field(..., description="Unique meeting identifier")
    title: str = Field(..., description="Meeting title")
    date: str = Field(..., description="Meeting date (YYYY-MM-DD)")
    participants: List[str] = Field(default_factory=list, description="List of participants")
    summary: str = Field(..., description="Executive summary")
    key_decisions: List[str] = Field(default_factory=list, description="Key decisions made")
    next_steps: List[str] = Field(default_factory=list, description="Next steps identified")

    @validator("meeting_id")
    def validate_meeting_id(cls, v):
        """Generate meeting ID if not provided"""
        if not v:
            return f"MTG-{datetime.now().strftime('%Y-%m-%d')}-{str(uuid4())[:8].upper()}"
        return v

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Meeting(BaseModel):
    """Complete meeting model with summary and tasks"""

    summary: MeetingSummary
    tasks: List["Task"] = Field(default_factory=list, description="Associated tasks")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")
    processed_at: datetime = Field(default_factory=datetime.now, description="Processing timestamp")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Forward reference resolution
from .task import Task
Meeting.update_forward_refs()