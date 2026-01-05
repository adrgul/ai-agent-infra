from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MessageRecord(BaseModel):
    role: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ChatRequest(BaseModel):
    user_id: str
    session_id: str
    message: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DebugInfo(BaseModel):
    request_json: Dict[str, Any]
    user_id: str
    session_id: str
    user_query: str
    rag_context: List[str]
    final_llm_prompt: str


class ChatResponse(BaseModel):
    reply: str
    user_id: str
    session_id: str
    history: List[MessageRecord]
    debug: DebugInfo


class UserProfile(BaseModel):
    user_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    preferences: Dict[str, Any] = Field(default_factory=dict)

    def touch(self) -> None:
        self.updated_at = datetime.utcnow()
