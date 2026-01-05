"""Domain interfaces - Abstract base classes (SOLID: Dependency Inversion)"""

from abc import ABC, abstractmethod
from typing import List

from domain.models import DocumentChunk, SearchResult, Answer


class VectorStoreInterface(ABC):
    """Vector store abstract interface"""
    
    @abstractmethod
    def add_chunks(self, chunks: List[DocumentChunk]) -> None:
        """Chunk-ok hozzáadása a vector store-hoz"""
        pass
    
    @abstractmethod
    def search(self, query: str, top_k: int = 5) -> List[SearchResult]:
        """Szemantikus keresés"""
        pass
    
    @abstractmethod
    def get_collection_stats(self) -> dict:
        """Kollekcio statisztikák"""
        pass


class LLMClientInterface(ABC):
    """LLM client abstract interface"""
    
    @abstractmethod
    def generate_answer(
        self, 
        question: str, 
        context_chunks: List[SearchResult]
    ) -> str:
        """Válasz generálás kontextus alapján"""
        pass
    
    @abstractmethod
    def generate_embedding(self, text: str) -> List[float]:
        """Text embedding generálás"""
        pass


class DocumentLoaderInterface(ABC):
    """Document loader abstract interface"""
    
    @abstractmethod
    def load_documents(self, directory: str, domain: str) -> List[DocumentChunk]:
        """Dokumentumok betöltése és chunkolása"""
        pass

