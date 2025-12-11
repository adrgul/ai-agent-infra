"""
Domain interfaces - abstract base classes for repositories and clients.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from .models import Message, Citation, UserProfile


class IUserRepository(ABC):
    """User profile storage interface."""

    @abstractmethod
    async def get_profile(self, user_id: str) -> UserProfile:
        pass

    @abstractmethod
    async def save_profile(self, profile: UserProfile) -> UserProfile:
        pass

    @abstractmethod
    async def update_profile(self, user_id: str, updates: Dict[str, Any]) -> UserProfile:
        pass


class IConversationRepository(ABC):
    """Conversation history storage interface."""

    @abstractmethod
    async def get_history(self, session_id: str) -> List[Message]:
        pass

    @abstractmethod
    async def save_message(self, session_id: str, message: Message) -> None:
        pass

    @abstractmethod
    async def clear_history(self, session_id: str) -> None:
        pass

    @abstractmethod
    async def search_messages(self, query: str) -> List[Message]:
        pass


class IVectorStore(ABC):
    """Vector database interface."""

    @abstractmethod
    async def retrieve(self, query: str, top_k: int = 5) -> List[Citation]:
        pass

    @abstractmethod
    async def upsert(self, doc_id: str, content: str, metadata: Dict[str, Any]) -> None:
        pass


class IRAGClient(ABC):
    """RAG retrieval client interface."""

    @abstractmethod
    async def retrieve_for_domain(self, domain: str, query: str, top_k: int = 5) -> List[Citation]:
        pass
