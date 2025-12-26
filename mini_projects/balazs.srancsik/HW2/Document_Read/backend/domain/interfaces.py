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


class IWeatherClient(IToolClient):
    """Interface for weather service."""
    
    @abstractmethod
    async def get_forecast(self, city: Optional[str] = None, lat: Optional[float] = None, lon: Optional[float] = None) -> Dict[str, Any]:
        """Get weather forecast."""
        pass


class IGeocodeClient(IToolClient):
    """Interface for geocoding service."""
    
    @abstractmethod
    async def geocode(self, address: str) -> Dict[str, Any]:
        """Convert address to coordinates."""
        pass
    
    @abstractmethod
    async def reverse_geocode(self, lat: float, lon: float) -> Dict[str, Any]:
        """Convert coordinates to address."""
        pass


class IIPGeolocationClient(IToolClient):
    """Interface for IP geolocation."""
    
    @abstractmethod
    async def get_location(self, ip_address: str) -> Dict[str, Any]:
        """Get location from IP address."""
        pass


class IFXRatesClient(IToolClient):
    """Interface for foreign exchange rates."""
    
    @abstractmethod
    async def get_rate(self, base: str, target: str, date: Optional[str] = None) -> Dict[str, Any]:
        """Get exchange rate."""
        pass


class ICryptoPriceClient(IToolClient):
    """Interface for cryptocurrency prices."""
    
    @abstractmethod
    async def get_price(self, symbol: str, fiat: str = "USD") -> Dict[str, Any]:
        """Get crypto price."""
        pass


class IRadioBrowserClient(IToolClient):
    """Interface for radio browser service."""
    
    @abstractmethod
    async def search_stations(
        self,
        name: Optional[str] = None,
        country: Optional[str] = None,
        country_code: Optional[str] = None,
        language: Optional[str] = None,
        tag: Optional[str] = None,
        order: str = "votes",
        limit: int = 10
    ) -> Dict[str, Any]:
        """Advanced search for radio stations with multiple filters."""
        pass
    
    @abstractmethod
    async def get_top_stations(self, by: str = "votes", limit: int = 10) -> Dict[str, Any]:
        """Get top stations by votes, clicks, or recent activity."""
        pass
    
    @abstractmethod
    async def get_countries(self) -> Dict[str, Any]:
        """Get list of available countries with station counts."""
        pass
    
    @abstractmethod
    async def get_languages(self) -> Dict[str, Any]:
        """Get list of available languages with station counts."""
        pass
    
    @abstractmethod
    async def get_tags(self, filter_tag: Optional[str] = None) -> Dict[str, Any]:
        """Get list of available tags/genres with station counts."""
        pass


class IBookRAGClient(IToolClient):
    """Interface for book RAG (Retrieval-Augmented Generation) service."""
    
    @abstractmethod
    async def query(self, question: str, top_k: int = 5) -> Dict[str, Any]:
        """Query the book content using RAG pipeline."""
        pass
    
    @abstractmethod
    async def get_book_info(self) -> Dict[str, Any]:
        """Get information about the loaded book."""
        pass
