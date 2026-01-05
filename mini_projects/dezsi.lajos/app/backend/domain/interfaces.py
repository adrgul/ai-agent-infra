from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from .models import Message, TicketCreate

class ILLMClient(ABC):
    @abstractmethod
    async def generate(self, prompt: str) -> str:
        pass
    
    @abstractmethod
    async def generate_structured(self, prompt: str, response_model: Any) -> Any:
        pass

class IVectorDBClient(ABC):
    @abstractmethod
    async def search(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def upsert(self, text: str, metadata: Dict[str, Any]):
        pass

class IConversationRepository(ABC):
    @abstractmethod
    async def add_message(self, conversation_id: str, message: Message):
        pass
    
    @abstractmethod
    async def get_history(self, conversation_id: str) -> List[Message]:
        pass
    
    @abstractmethod
    async def clear_history(self, conversation_id: str):
        pass

class ITicketClient(ABC):
    @abstractmethod
    async def create_ticket(self, ticket: TicketCreate) -> Dict[str, Any]:
        """Creates a ticket in the external system and returns the response details (e.g. ID, URL)."""
        pass
