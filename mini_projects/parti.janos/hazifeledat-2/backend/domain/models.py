from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

# --- User Models ---
class UserPreferences(BaseModel):
    language: str = "hu"
    theme: str = "light"

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    role: str = "employee"
    department: str = "general"
    preferences: UserPreferences = Field(default_factory=UserPreferences)
    created_at: datetime = Field(default_factory=datetime.now)

# --- Chat Models ---
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    user_id: str = "guest"

class Message(BaseModel):
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)

class Citation(BaseModel):
    """Citation model for document sources."""
    doc_id: str = Field(description="Document identifier")
    title: str = Field(description="Document title or source name")
    score: float = Field(description="Relevance score (0.0 - 1.0)")
    snippet: Optional[str] = Field(None, description="Relevant text snippet")
    url: Optional[str] = Field(None, description="URL to the document if available")
    source: Optional[str] = Field(None, description="Source file name")

class ChatResponse(BaseModel):
    response: str
    session_id: str
    tool_used: Optional[str] = None
    citations: List[Citation] = Field(default_factory=list, description="Document citations")
    domain: Optional[str] = Field(None, description="Detected domain")

# --- Document Models ---
class DocumentMetadata(BaseModel):
    source: str
    domain: str
    created_at: str
    access_level: str = "all"

class DocumentChunk(BaseModel):
    id: str
    content: str
    metadata: DocumentMetadata
    vector: Optional[List[float]] = None
