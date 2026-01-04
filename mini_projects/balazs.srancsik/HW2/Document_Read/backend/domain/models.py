"""
Domain models - Core business entities.
Following SOLID: Single Responsibility Principle - each model has one clear purpose.
"""
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field


class Message(BaseModel):
    """Represents a single message in the conversation."""
    role: Literal["user", "assistant", "system", "tool"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = None


class UserProfile(BaseModel):
    """User profile stored persistently. Never deleted, only updated."""
    user_id: str
    language: str = "hu"
    default_city: str = "Budapest"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    preferences: Dict[str, Any] = Field(default_factory=dict)


class ConversationHistory(BaseModel):
    """Session-specific conversation history. Can be reset without deleting profile."""
    session_id: str
    messages: List[Message] = Field(default_factory=list)
    summary: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class WorkflowState(BaseModel):
    """Generic workflow state for multi-step processes."""
    flow: Optional[str] = None
    step: int = 0
    total_steps: int = 0
    data: Dict[str, Any] = Field(default_factory=dict)


class Memory(BaseModel):
    """Complete memory context for the agent."""
    chat_history: List[Message] = Field(default_factory=list)
    preferences: Dict[str, Any] = Field(default_factory=dict)
    workflow_state: WorkflowState = Field(default_factory=WorkflowState)


class ToolCall(BaseModel):
    """Record of a tool invocation."""
    tool_name: str
    arguments: Dict[str, Any]
    result: Optional[Any] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class ChatRequest(BaseModel):
    """Incoming chat request from frontend."""
    user_id: str
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Response sent back to frontend."""
    final_answer: str
    tools_used: List[Dict[str, Any]] = Field(default_factory=list)
    memory_snapshot: Dict[str, Any] = Field(default_factory=dict)
    logs: Optional[List[str]] = None


class ProfileUpdateRequest(BaseModel):
    """Request to update user profile."""
    language: Optional[str] = None
    default_city: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None


class SearchResult(BaseModel):
    """Search result from history search."""
    session_id: str
    snippet: str
    timestamp: datetime
    role: str
