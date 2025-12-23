"""
Prompt templates for RAG chat.

Why this module exists:
- Centralizes prompt engineering for RAG question answering
- Formats retrieved context with source attribution
- Provides clear instructions to LLM about using only provided context

Design decisions:
- System message establishes RAG behavior (only use context, say "I don't know" if not in context)
- Context formatting includes source identifiers for attribution
- No conversation history (each question is independent)
"""

from typing import List

from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, SystemMessage

from app.core.logging import get_logger

logger = get_logger(__name__)

# Why system message: Sets LLM behavior to answer from context only
# and admit when information is not available
SYSTEM_PROMPT = """You are a helpful assistant that answers questions based ONLY on the provided context.

Rules:
1. Answer the question using ONLY information from the context below
2. If the answer is not in the context, say "I don't know based on the provided documentation"
3. Be concise and direct in your answers
4. When referencing information, you may mention which document it comes from

Do not use any external knowledge or make assumptions beyond what's explicitly stated in the context."""


def build_rag_prompt(
    query: str,
    context_chunks: List[Document],
) -> List[SystemMessage | HumanMessage]:
    """
    Build RAG prompt with system message, context, and user query.

    Why this function: Constructs prompt that:
    1. Sets LLM behavior via system message
    2. Provides retrieved context with source attribution
    3. Presents user's question

    Why source identifiers: Each chunk is labeled with [filename | chunk_id]
    so LLM can reference sources in its answer, and we can trace which
    chunks influenced the response.

    Why list of messages: Modern chat models expect message list format
    (system, user, assistant) rather than single string.

    Args:
        query: User's question
        context_chunks: Retrieved chunks from vector store

    Returns:
        List of messages: [SystemMessage, HumanMessage with context + query]
    """
    # Assert: Must have query and at least one context chunk
    assert query.strip(), "Query must not be empty"
    assert len(context_chunks) > 0, "Must provide at least one context chunk"

    logger.debug(f"Building RAG prompt with {len(context_chunks)} context chunks")

    # Format context chunks with source attribution
    # Why enumerate and label: Makes it easy to see which chunk is which
    context_parts = []
    for i, chunk in enumerate(context_chunks, 1):
        filename = chunk.metadata.get("filename", "unknown")
        chunk_id = chunk.metadata.get("chunk_id", f"unknown:{i}")

        # Why [filename | chunk_id]: Clear visual separator for source info
        context_parts.append(
            f"[Source: {filename} | {chunk_id}]\n{chunk.page_content}"
        )

    # Join all context chunks
    # Why double newline: Visual separation between chunks
    context_text = "\n\n".join(context_parts)

    # Build human message with context and query
    # Why format: Clearly delineates context section from question
    human_message_content = f"""Context:
{context_text}

Question: {query}"""

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=human_message_content),
    ]

    logger.debug(f"RAG prompt built: {len(context_text)} chars of context")

    return messages
