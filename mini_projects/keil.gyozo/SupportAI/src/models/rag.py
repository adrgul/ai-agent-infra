"""RAG document models."""

from typing import Optional
from pydantic import BaseModel, Field, HttpUrl


class RAGDocument(BaseModel):
    """Retrieved document from vector search."""

    doc_id: str = Field(..., description="Document identifier")
    chunk_id: str = Field(..., description="Chunk identifier")
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Document content/chunk text")
    url: str = Field(..., description="Knowledge base URL")
    score: float = Field(..., ge=0, le=1, description="Similarity score")
    category: Optional[str] = Field(None, description="Document category")
    subcategory: Optional[str] = Field(None, description="Document subcategory")
    doc_type: Optional[str] = Field(None, description="Type: kb_article | faq | policy")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "doc_id": "KB-1234",
                    "chunk_id": "KB-1234-c-45",
                    "title": "How to Handle Duplicate Charges",
                    "content": "Duplicate charges are typically resolved within 3-5 business days...",
                    "url": "https://kb.company.com/billing/duplicate-charges",
                    "score": 0.89,
                    "category": "billing",
                    "subcategory": "duplicate_charge",
                    "doc_type": "kb_article"
                }
            ]
        }
    }


class RerankedDocument(BaseModel):
    """Document after re-ranking with cross-encoder."""

    doc_id: str
    chunk_id: str
    title: str
    content: str
    url: str
    original_score: float = Field(..., description="Original vector search score")
    rerank_score: float = Field(..., description="Re-ranking score")
    final_score: float = Field(..., description="Combined final score")
    rank: int = Field(..., ge=1, description="Final ranking position")

    @classmethod
    def from_rag_document(
        cls,
        doc: RAGDocument,
        rerank_score: float,
        rank: int,
        alpha: float = 0.5
    ) -> "RerankedDocument":
        """Create from RAGDocument with re-ranking score.

        Args:
            doc: Original RAG document
            rerank_score: Score from re-ranker (0-1)
            rank: Final ranking position
            alpha: Weight for combining scores (0=only rerank, 1=only original)
        """
        final_score = alpha * doc.score + (1 - alpha) * rerank_score

        return cls(
            doc_id=doc.doc_id,
            chunk_id=doc.chunk_id,
            title=doc.title,
            content=doc.content,
            url=doc.url,
            original_score=doc.score,
            rerank_score=rerank_score,
            final_score=final_score,
            rank=rank
        )


class Citation(BaseModel):
    """Citation reference for generated answers."""

    doc_id: str = Field(..., description="Document identifier")
    chunk_id: str = Field(..., description="Chunk identifier")
    title: str = Field(..., description="Document title")
    score: float = Field(..., ge=0, le=1, description="Relevance score")
    url: str = Field(..., description="Knowledge base URL")
    cited_text: Optional[str] = Field(None, description="Specific text that was cited")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "doc_id": "KB-1234",
                    "chunk_id": "KB-1234-c-45",
                    "title": "Duplicate Charge Resolution",
                    "score": 0.89,
                    "url": "https://kb.company.com/billing/duplicate",
                    "cited_text": "Duplicate charges are resolved within 3-5 business days"
                }
            ]
        }
    }
