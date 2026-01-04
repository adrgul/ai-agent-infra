"""Domain interfaces (abstract contracts)."""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any, Literal
from datetime import datetime

from .models import (
    Chunk, RetrievedChunk, CategoryDecision, 
    UserProfile, UploadedDocument, Message
)


class ActivityCallback(ABC):
    """Interface for activity logging callbacks."""

    @abstractmethod
    async def log_activity(
        self, 
        message: str, 
        activity_type: Literal["info", "processing", "success", "warning", "error"] = "info",
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log an activity event with optional metadata."""
        pass


class EmbeddingService(ABC):
    """Interface for embedding service."""

    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        """Embed a single text."""
        pass

    @abstractmethod
    async def embed_texts(
        self, texts: List[str], batch_size: int = 100
    ) -> List[List[float]]:
        """Embed multiple texts in batches."""
        pass


class VectorStore(ABC):
    """Interface for vector database operations."""

    @abstractmethod
    async def create_collection(self, collection_name: str) -> None:
        """Create or get a collection."""
        pass

    @abstractmethod
    async def add_chunks(
        self, collection_name: str, chunks: List[Chunk],
        embeddings: List[List[float]] = None
    ) -> None:
        """Add chunks to a collection with optional embeddings."""
        pass

    @abstractmethod
    async def query(
        self, collection_name: str, query_embedding: List[float], 
        top_k: int = 5
    ) -> List[RetrievedChunk]:
        """Query top-k similar chunks."""
        pass

    @abstractmethod
    async def delete_chunks(
        self, collection_name: str, chunk_ids: List[str]
    ) -> None:
        """Delete chunks by IDs."""
        pass

    @abstractmethod
    async def delete_collection(self, collection_name: str) -> None:
        """Delete an entire collection."""
        pass


class Chunker(ABC):
    """Interface for document chunking."""

    @abstractmethod
    def chunk_text(
        self, text: str, chunk_size_tokens: int = 900, 
        overlap_tokens: int = 150
    ) -> List[str]:
        """Split text into chunks."""
        pass


class DocumentTextExtractor(ABC):
    """Interface for extracting text from documents."""

    @abstractmethod
    async def extract_text(self, file_path: str) -> str:
        """Extract text from a document."""
        pass


class CategoryRouter(ABC):
    """Interface for LLM-based category routing."""

    @abstractmethod
    async def decide_category(
        self, question: str, available_categories: List[str]
    ) -> CategoryDecision:
        """Decide which category to search based on question."""
        pass


class RAGAnswerer(ABC):
    """Interface for RAG-based answer generation."""

    @abstractmethod
    async def generate_answer(
        self, question: str, context_chunks: List[RetrievedChunk],
        category: str
    ) -> str:
        """Generate answer from context chunks with citations."""
        pass


class UserProfileRepository(ABC):
    """Interface for user profile persistence."""

    @abstractmethod
    async def get_profile(self, user_id: str) -> Optional[UserProfile]:
        """Load user profile."""
        pass

    @abstractmethod
    async def save_profile(self, profile: UserProfile) -> None:
        """Save user profile (atomic write)."""
        pass


class SessionRepository(ABC):
    """Interface for session history persistence."""

    @abstractmethod
    async def get_messages(self, session_id: str) -> List[Message]:
        """Load conversation messages."""
        pass

    @abstractmethod
    async def append_message(self, session_id: str, message: Message) -> None:
        """Append a message to session (atomic write)."""
        pass

    @abstractmethod
    async def clear_messages(self, session_id: str) -> None:
        """Clear all messages in session."""
        pass


class UploadRepository(ABC):
    """Interface for uploaded document file management."""

    @abstractmethod
    def save_upload(
        self, user_id: str, category: str, upload_id: str,
        filename: str, content: bytes
    ) -> str:
        """Save uploaded file. Return file path."""
        pass

    @abstractmethod
    def get_upload_path(
        self, user_id: str, category: str, upload_id: str, filename: str
    ) -> str:
        """Get path to saved upload."""
        pass

    @abstractmethod
    def delete_upload(
        self, user_id: str, category: str, upload_id: str, filename: str
    ) -> None:
        """Delete uploaded file and derived artifacts."""
        pass

    @abstractmethod
    async def list_uploads(
        self, user_id: str, category: str
    ) -> List[UploadedDocument]:
        """List uploads for a user and category."""
        pass

    @abstractmethod
    async def save_chunks(
        self, user_id: str, category: str, upload_id: str, 
        chunks: List[Chunk]
    ) -> None:
        """Save chunks.json to derived artifacts folder."""
        pass

    @abstractmethod
    async def load_chunks(
        self, user_id: str, category: str, upload_id: str
    ) -> List[Chunk]:
        """Load chunks.json from derived artifacts folder."""
        pass

    @abstractmethod
    async def get_categories(self) -> List[str]:
        """Get list of all available categories (global, not user-specific)."""
        pass

    @abstractmethod
    async def delete_category(self, category: str) -> None:
        """Delete entire category with all uploads and derived artifacts."""
        pass
