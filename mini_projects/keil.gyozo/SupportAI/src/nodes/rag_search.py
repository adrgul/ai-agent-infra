"""RAG search node - retrieves relevant documents from vector database."""

import logging
from typing import Optional

from ..models.state import SupportTicketState
from ..models.rag import RAGDocument
from ..services import QdrantService, EmbeddingService

logger = logging.getLogger(__name__)


async def rag_search_node(
    state: SupportTicketState,
    qdrant_service: Optional[QdrantService] = None,
    embedding_service: Optional[EmbeddingService] = None,
    top_k: int = 10,
    score_threshold: float = 0.7
) -> dict:
    """Search knowledge base for relevant documents using vector similarity.

    This node performs hybrid search:
    1. Generates embeddings for each search query
    2. Searches Qdrant vector database
    3. Optionally filters by category
    4. Deduplicates results by chunk_id
    5. Returns top-k most relevant documents

    Args:
        state: Current workflow state with search_queries and category
        qdrant_service: Qdrant service instance (injected by workflow)
        embedding_service: Embedding service instance (injected by workflow)
        top_k: Number of documents to retrieve per query
        score_threshold: Minimum similarity score (0-1)

    Returns:
        Dictionary with retrieved_docs list
    """
    logger.info(f"Searching knowledge base for ticket: {state.get('ticket_id')}")

    # Initialize services if not provided
    if qdrant_service is None:
        qdrant_service = QdrantService()
    if embedding_service is None:
        embedding_service = EmbeddingService()

    search_queries = state.get("search_queries", [])
    if not search_queries:
        logger.warning("No search queries provided, using raw message")
        search_queries = [state["raw_message"][:200]]

    category = state.get("category")
    all_docs: dict[str, dict] = {}  # chunk_id -> document (for deduplication)

    try:
        # Search for each query
        for i, query in enumerate(search_queries, 1):
            logger.debug(f"Searching query {i}/{len(search_queries)}: {query}")

            # Generate embedding
            query_vector = await embedding_service.embed_query(query)

            # Search Qdrant
            results = await qdrant_service.search(
                query_vector=query_vector,
                top_k=top_k,
                category_filter=category if category else None,
                score_threshold=score_threshold
            )

            # Deduplicate by chunk_id (keep highest score)
            for doc in results:
                chunk_id = doc["chunk_id"]
                if chunk_id not in all_docs or doc["score"] > all_docs[chunk_id]["score"]:
                    all_docs[chunk_id] = doc

        # Sort by score and return top results
        sorted_docs = sorted(
            all_docs.values(),
            key=lambda x: x["score"],
            reverse=True
        )[:top_k]

        logger.info(
            f"Retrieved {len(sorted_docs)} unique documents "
            f"(from {len(search_queries)} queries)"
        )

        # Validate documents with Pydantic
        validated_docs = [
            RAGDocument(**doc).model_dump() for doc in sorted_docs
        ]

        return {
            "retrieved_docs": validated_docs
        }

    except Exception as e:
        logger.error(f"RAG search failed: {e}")
        return {
            "retrieved_docs": [],
            "errors": [f"RAG search error: {str(e)}"]
        }
