"""
Domain models - Pydantic data structures for requests/responses.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class DomainType(str, Enum):
    """Supported knowledge domains."""
    HR = "hr"
    IT = "it"
    FINANCE = "finance"
    LEGAL = "legal"
    MARKETING = "marketing"
    GENERAL = "general"


class Message(BaseModel):
    """Single message in conversation history."""
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = None


class Citation(BaseModel):
    """Source document reference."""
    doc_id: str
    title: str
    score: float  # Retrieval score (0-1)
    url: Optional[str] = None


class WorkflowState(BaseModel):
    """Multi-step workflow tracking."""
    flow: Optional[str] = None  # e.g., "hr_vacation_request"
    step: int = 0
    total_steps: int = 0
    data: Optional[Dict[str, Any]] = None


class UserProfile(BaseModel):
    """User profile and preferences."""
    user_id: str
    organisation: str
    language: str = "hu"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    preferences: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_123",
                "organisation": "ACME Corp",
                "language": "hu",
                "preferences": {"department": "IT", "role": "engineer"}
            }
        }


class QueryRequest(BaseModel):
    """Chat query request."""
    user_id: str
    session_id: Optional[str] = None
    query: str
    organisation: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "emp_001",
                "query": "Szeretnék szabadságot igényelni október 3-4 között"
            }
        }


class ToolCall(BaseModel):
    """Tool invocation record."""
    tool_name: str
    arguments: Dict[str, Any]
    result: Optional[Any] = None
    error: Optional[str] = None


class QueryResponse(BaseModel):
    """Structured agent response."""
    domain: DomainType
    answer: str
    citations: List[Citation] = Field(default_factory=list)
    tools_used: List[ToolCall] = Field(default_factory=list)
    workflow: Optional[Dict[str, Any]] = None
    confidence: float = 1.0

    class Config:
        json_schema_extra = {
            "example": {
                "domain": "hr",
                "answer": "Szabadságkérelmed rögzítésre került október 3-4 között.",
                "citations": [
                    {
                        "doc_id": "HR-POL-001",
                        "title": "Vacation Policy",
                        "score": 0.94,
                        "url": "https://..."
                    }
                ],
                "workflow": {
                    "action": "hr_request_created",
                    "file": "hr_request_2025-10-03.json"
                }
            }
        }


class Memory(BaseModel):
    """Agent memory context."""
    chat_history: List[Message] = Field(default_factory=list)
    preferences: Dict[str, Any] = Field(default_factory=dict)
    workflow_state: WorkflowState = Field(default_factory=WorkflowState)
