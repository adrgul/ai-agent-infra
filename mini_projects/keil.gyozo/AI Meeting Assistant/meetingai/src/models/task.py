"""
Task data models using Pydantic
"""

from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, validator


class Task(BaseModel):
    """Model for individual task data"""

    task_id: str = Field(..., description="Unique task identifier")
    title: str = Field(..., description="Task title/description")
    assignee: str = Field(..., description="Person assigned to the task")
    due_date: Optional[str] = Field(None, description="Due date (YYYY-MM-DD)")
    priority: str = Field("Medium", description="Task priority")
    status: str = Field("to-do", description="Task status")
    meeting_reference: str = Field(..., description="Reference to originating meeting")
    description: Optional[str] = Field(None, description="Detailed description")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")

    @validator("task_id")
    def validate_task_id(cls, v):
        """Generate task ID if not provided"""
        if not v:
            return f"TASK-{str(uuid4())[:8].upper()}"
        return v

    @validator("priority")
    def validate_priority(cls, v):
        """Validate priority values"""
        valid_priorities = ["Low", "Medium", "High", "P1", "P2", "P3"]
        if v not in valid_priorities:
            raise ValueError(f"Priority must be one of: {valid_priorities}")
        return v

    @validator("status")
    def validate_status(cls, v):
        """Validate status values"""
        valid_statuses = ["to-do", "in-progress", "done", "cancelled"]
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of: {valid_statuses}")
        return v

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TaskList(BaseModel):
    """Model for a collection of tasks"""

    tasks: List[Task] = Field(default_factory=list, description="List of tasks")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")

    def get_tasks_by_assignee(self, assignee: str) -> List[Task]:
        """Get tasks assigned to a specific person"""
        return [task for task in self.tasks if task.assignee == assignee]

    def get_tasks_by_status(self, status: str) -> List[Task]:
        """Get tasks with a specific status"""
        return [task for task in self.tasks if task.status == status]

    def get_overdue_tasks(self) -> List[Task]:
        """Get tasks that are overdue"""
        today = datetime.now().date()
        overdue = []
        for task in self.tasks:
            if task.due_date:
                try:
                    due = datetime.fromisoformat(task.due_date).date()
                    if due < today and task.status != "done":
                        overdue.append(task)
                except ValueError:
                    continue
        return overdue