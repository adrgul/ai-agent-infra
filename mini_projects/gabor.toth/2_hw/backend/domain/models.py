"""Domain models for RAG agent application."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Any, Dict
from enum import Enum


class MessageRole(str, Enum):
    """Message role types."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


@dataclass
class Message:
    """Conversation message."""
    role: MessageRole
    content: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    user_id: Optional[str] = None  # User ID for user messages

    def to_dict(self) -> Dict[str, Any]:
        # Build result with proper key ordering
        result = {}
        result["role"] = self.role.value
        if self.user_id:
            result["user_id"] = self.user_id
        result["content"] = self.content
        result["timestamp"] = self.timestamp.isoformat()
        result["metadata"] = self.metadata
        return result


@dataclass
class UserProfile:
    """User profile stored on disk."""
    user_id: str
    language: str = "hu"
    categories: List[str] = field(default_factory=list)
    preferences: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "language": self.language,
            "categories": self.categories,
            "preferences": self.preferences,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class Chunk:
    """Document chunk for vector indexing."""
    chunk_id: str
    content: str
    upload_id: str
    category: str
    source_file: str
    chunk_index: int
    start_char: int
    end_char: int
    section_title: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "content": self.content,
            "upload_id": self.upload_id,
            "category": self.category,
            "source_file": self.source_file,
            "chunk_index": self.chunk_index,
            "start_char": self.start_char,
            "end_char": self.end_char,
            "section_title": self.section_title,
            "metadata": self.metadata,
        }


@dataclass
class UploadedDocument:
    """Uploaded document metadata."""
    upload_id: str
    user_id: str
    filename: str
    category: str
    size: int
    created_at: datetime
    chunk_size_tokens: int = 900
    overlap_tokens: int = 150
    embedding_batch_size: int = 100
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "upload_id": self.upload_id,
            "user_id": self.user_id,
            "filename": self.filename,
            "category": self.category,
            "size": self.size,
            "created_at": self.created_at.isoformat(),
            "chunk_size_tokens": self.chunk_size_tokens,
            "overlap_tokens": self.overlap_tokens,
            "embedding_batch_size": self.embedding_batch_size,
            "metadata": self.metadata,
        }


@dataclass
class RetrievedChunk:
    """Retrieved chunk with similarity score."""
    chunk_id: str
    content: str
    distance: float
    metadata: Dict[str, Any]
    snippet: Optional[str] = None


@dataclass
class CategoryDecision:
    """LLM decision on which category to search."""
    category: Optional[str]
    reason: str


@dataclass
class RAGResponse:
    """RAG response with citations and debug info."""
    final_answer: str
    tools_used: List[Dict[str, str]]
    memory_snapshot: Dict[str, Any]
    rag_debug: Optional[Dict[str, Any]] = None
