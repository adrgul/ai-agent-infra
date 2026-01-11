from typing import List, Optional
from pydantic import BaseModel, Field

class Task(BaseModel):
    """
    Represents an actionable task extracted from the meeting.
    """
    title: str = Field(description="The title or description of the task.")
    assignee: str = Field(default="Unassigned", description="The person responsible for the task.")
    priority: str = Field(description="Priority level of the task (e.g., High, Medium, Low).")
    due_date: Optional[str] = Field(default=None, description="Due date in ISO format if available.")

class MeetingNotes(BaseModel):
    """
    Structured meeting notes containing key points and decisions.
    """
    key_points: List[str] = Field(description="List of key points discussed in the meeting.")
    decisions: List[str] = Field(description="List of decisions made during the meeting.")
