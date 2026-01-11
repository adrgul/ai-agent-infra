"""Deterministic chunker

This chunker deterministically splits a document by whitespace into chunks of
`chunk_size` characters with `chunk_overlap` characters overlapped between
consecutive chunks.

Rationale / why: using character-based chunking is language-agnostic, simple,
and deterministic (no randomness). Overlap helps preserve context across
boundary splits; chunk_size/overlap are configurable and chosen to balance
context window vs. RAG recall.
"""
from dataclasses import dataclass
from typing import List, Dict


@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    text: str
    metadata: Dict


class DeterministicChunker:
    """Chunker that splits text deterministically by character counts.

    Not the most linguistically aware, but deterministic and easy to test.
    Tradeoffs:
      - Pros: deterministic, simple, portable
      - Cons: may split across sentences, which can be mitigated by tuning
        chunk_size and overlap.
    """

    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 128):
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be < chunk_size")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(self, doc_id: str, text: str, doc_metadata: Dict = None) -> List[Chunk]:
        """Return a list of Chunk objects for the given document text.

        Deterministic: same input text always yields same chunk ids and texts.
        Chunk ids are `doc_id:idx`.
        
        Args:
            doc_id: Document identifier
            text: Text content to chunk
            doc_metadata: Optional metadata to include in each chunk (e.g., title, source, page)
        """
        chunks: List[Chunk] = []
        start = 0
        idx = 0
        length = len(text)
        base_metadata = doc_metadata or {}
        
        while start < length:
            end = min(start + self.chunk_size, length)
            chunk_text = text[start:end]
            chunk_id = f"{doc_id}:{idx}"
            
            # Merge char offsets with provided doc metadata
            metadata = {**base_metadata, "start": start, "end": end, "chunk_index": idx}
            
            chunks.append(Chunk(chunk_id=chunk_id, doc_id=doc_id, text=chunk_text, metadata=metadata))
            if end == length:
                break
            start = end - self.chunk_overlap
            idx += 1
        return chunks
