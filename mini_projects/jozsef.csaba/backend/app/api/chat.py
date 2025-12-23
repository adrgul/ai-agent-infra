"""
Chat endpoint for RAG question answering.

Why this module exists:
- Provides API for asking questions against indexed documents
- Orchestrates RAG pipeline (retrieve + generate)
- Returns answer with source attributions

Design decisions:
- Returns 409 if vector store not indexed yet (directs user to /ingest)
- Stateless (no conversation history)
- Configurable top_k and temperature via request parameters
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.rag.chain import answer_question, create_chat_llm
from app.rag.embeddings import create_embeddings
from app.rag.vectorstore import vectorstore_exists
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter()
logger = get_logger(__name__)


@router.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(
    request: ChatRequest,
    settings: Settings = Depends(get_settings),
) -> ChatResponse:
    """
    Ask a question using RAG retrieval.

    Why this endpoint: Core functionality of the chatbot.
    Retrieves relevant document chunks and generates answer using LLM.

    Why 409 when index missing: Conflict status code indicates the resource
    (vector store) must be created before this operation can proceed.
    Directs user to call /ingest first.

    Why stateless: No conversation history. Each request is independent.
    session_id is accepted for UI correlation but not used for memory.

    Args:
        request: Chat request with message, top_k, temperature, optional session_id
        settings: Injected application settings

    Returns:
        ChatResponse: Answer with source attributions and model name

    Raises:
        HTTPException 409: Vector store not found (call /ingest first)
        HTTPException 500: RAG pipeline error
    """
    # Assert: request.message must not be empty
    # (Pydantic validates this via min_length=1)

    logger.info(f"Chat request: {request.message[:100]}... (top_k={request.top_k})")

    # Check if vector store exists
    # Why first: Fail fast if index not built yet
    if not vectorstore_exists(settings):
        logger.warning("Vector store not found, returning 409")
        raise HTTPException(
            status_code=409,
            detail="Vector store not found. Please call /ingest to build the index first.",
        )

    try:
        # Create embeddings and LLM
        # Why create per request: Could cache for production,
        # but recreating is acceptable for demo and ensures fresh config
        embeddings = create_embeddings(settings)
        llm = create_chat_llm(settings)

        # Call RAG pipeline
        # Why answer_question: Encapsulates retrieval + generation logic
        answer, sources = answer_question(
            query=request.message,
            top_k=request.top_k,
            temperature=request.temperature,
            settings=settings,
            embeddings=embeddings,
            llm=llm,
        )

        # Build response
        # Why echo session_id: Allows UI to correlate request/response
        return ChatResponse(
            session_id=request.session_id,
            answer=answer,
            sources=sources,
            model=settings.OPENAI_CHAT_MODEL,
        )

    except HTTPException:
        # Re-raise HTTP exceptions (like 409)
        raise

    except Exception as e:
        # Why 500: Unexpected errors in RAG pipeline
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate answer: {str(e)}",
        ) from e
