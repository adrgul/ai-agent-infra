"""Domain models - Data structures"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class DocumentChunk:
    """Dokumentum chunk model"""
    
    content: str
    domain: str  # it, hr, finance
    source: str  # file path
    chunk_id: int
    metadata: dict


@dataclass
class SearchResult:
    """Keresési eredmény model"""
    
    chunk: DocumentChunk
    score: float
    

@dataclass
class Answer:
    """Válasz model citációkkal"""
    
    question: str
    answer: str
    sources: List[SearchResult]
    confidence: float

