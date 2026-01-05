"""
Pydantic schemas for the /chat endpoint.

Why this module exists:
- Type-safe request/response contracts for RAG chat
- Validation of chat parameters (top_k range, temperature range)
- Source attribution schema for RAG transparency

Design decisions:
- session_id optional (for UI correlation, not used for memory)
- top_k and temperature have sensible defaults and bounds
- Sources include snippet for preview without full chunk retrieval
"""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    """
    Request schema for POST /chat.

    Why these fields:
    - session_id: Optional UI correlation ID (NOT used for conversation memory)
    - message: The user's question
    - top_k: Controls number of retrieved chunks (more = more context, slower)
    - temperature: LLM sampling temperature (0 = deterministic, 1 = creative)

    Why no history: Spec requires stateless operation; each question is independent.
    """

    # Assert: message must not be empty
    # (Pydantic min_length enforces this)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "session_id": "user-123-session",
                "message": "What does the documentation say about deployment?",
                "top_k": 4,
                "temperature": 0.2
            }
        }
    )

    session_id: Optional[str] = Field(
        default=None,
        description="Optional session ID for UI correlation (not used for memory)"
    )

    message: str = Field(
        ...,
        min_length=1,
        description="User's question or message"
    )

    top_k: int = Field(
        default=4,
        ge=1,  # At least 1 chunk
        le=20,  # Max 20 chunks (balance context vs token usage)
        description="Number of document chunks to retrieve for context"
    )

    temperature: float = Field(
        default=0.2,
        ge=0.0,
        le=1.0,
        description="LLM temperature (0=deterministic, 1=creative)"
    )


class SourceAttribution(BaseModel):
    """
    Source attribution for a retrieved chunk.

    Why these fields:
    - source_id: Unique identifier for the chunk (filename:chunk_index)
    - filename: User-friendly file reference
    - snippet: Preview of chunk content (~240 chars) for UI display

    Why snippet length: Enough to preview context, not so long that
    response payload becomes large with many sources.
    """

    # Assert: source_id and filename must not be empty
    # (Validated in business logic before creating SourceAttribution)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "source_id": "deployment.md:2",
                "filename": "deployment.md",
                "snippet": "To deploy on Cloud Run, use the following command..."
            }
        }
    )

    source_id: str = Field(
        ...,
        description="Unique chunk identifier (format: filename:index)"
    )

    filename: str = Field(
        ...,
        description="Source filename"
    )

    snippet: str = Field(
        ...,
        description="First ~240 characters of chunk content"
    )


class ChatResponse(BaseModel):
    """
    Response schema for POST /chat.

    Why these fields:
    - session_id: Echoed back for UI correlation
    - answer: The generated response from the LLM
    - sources: List of retrieved chunks for transparency and verification
    - model: Which model generated the answer (useful for debugging/logging)
    """

    # Assert: answer must not be empty, sources list must be present
    # (Business logic ensures this before constructing response)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "session_id": "user-123-session",
                "answer": "According to the documentation, you can deploy on Cloud Run...",
                "sources": [
                    {
                        "source_id": "deployment.md:2",
                        "filename": "deployment.md",
                        "snippet": "To deploy on Cloud Run, use..."
                    }
                ],
                "model": "gpt-4.1-mini"
            }
        }
    )

    session_id: Optional[str] = Field(
        default=None,
        description="Echoed session ID from request"
    )

    answer: str = Field(
        ...,
        min_length=1,
        description="Generated answer from the LLM"
    )

    sources: List[SourceAttribution] = Field(
        ...,
        description="List of retrieved source chunks used for context"
    )

    model: str = Field(
        ...,
        description="Model that generated the answer"
    )
