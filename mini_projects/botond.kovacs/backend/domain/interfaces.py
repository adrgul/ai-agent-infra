"""
Domain interfaces - Abstractions for repositories and services.
Following SOLID: Dependency Inversion Principle - depend on abstractions, not concrete implementations.
Interface Segregation Principle - specific interfaces for different concerns.
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from domain.models import UserProfile, ConversationHistory, Message, SearchResult


class IUserRepository(ABC):
    """Interface for user profile persistence."""
    
    @abstractmethod
    async def get_profile(self, user_id: str) -> UserProfile:
        """Load or create user profile."""
        pass
    
    @abstractmethod
    async def save_profile(self, profile: UserProfile) -> None:
        """Save user profile to storage."""
        pass
    
    @abstractmethod
    async def update_profile(self, user_id: str, updates: Dict[str, Any]) -> UserProfile:
        """Update specific fields of user profile."""
        pass


class IConversationRepository(ABC):
    """Interface for conversation history persistence."""
    
    @abstractmethod
    async def get_history(self, session_id: str) -> ConversationHistory:
        """Load or create conversation history."""
        pass
    
    @abstractmethod
    async def save_history(self, history: ConversationHistory) -> None:
        """Save conversation history to storage."""
        pass
    
    @abstractmethod
    async def add_message(self, session_id: str, message: Message) -> None:
        """Append a message to conversation history."""
        pass
    
    @abstractmethod
    async def clear_history(self, session_id: str) -> None:
        """Clear conversation history (reset context)."""
        pass
    
    @abstractmethod
    async def search_messages(self, query: str) -> List[SearchResult]:
        """Search across all conversations."""
        pass


class IToolClient(ABC):
    """Base interface for external tool clients."""
    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool with given parameters."""
        pass


# --- Gas Exported Quantity Tool Interface ---
class IGasExportClient(IToolClient):
    """Interface for gas exported quantity tool (Transparency.host)."""
    @abstractmethod
    async def get_exported_quantity(self, point_label: str, date_from: str, date_to: str) -> Dict[str, Any]:
        """Fetch exported gas quantity in kWh for a given point and date range."""
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool with given parameters."""
        pass


class IRegulationRAGClient(IToolClient):
    """Interface for regulation RAG (Retrieval-Augmented Generation) service."""
    
    @abstractmethod
    async def query(self, question: str, top_k: int = 5) -> Dict[str, Any]:
        """Query the regulation content using RAG pipeline."""
        pass
    
    @abstractmethod
    async def get_regulation_info(self) -> Dict[str, Any]:
        """Get information about the loaded regulation."""
        pass
