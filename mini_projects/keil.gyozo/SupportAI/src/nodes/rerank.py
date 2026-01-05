"""Re-ranking node - re-scores documents using LLM for better relevance."""

import logging

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from ..models.state import SupportTicketState
from ..models.rag import RAGDocument, RerankedDocument
from ..services import get_llm

logger = logging.getLogger(__name__)


class RelevanceScore(BaseModel):
    """Structured output for document relevance scoring."""

    relevance_score: float = Field(
        ...,
        ge=0,
        le=1,
        description="Relevance score from 0 (not relevant) to 1 (highly relevant)"
    )
    reasoning: str = Field(..., description="Brief explanation for the score")


async def rerank_node(
    state: SupportTicketState,
    top_n: int = 3,
    alpha: float = 0.5
) -> dict:
    """Re-rank retrieved documents using LLM for improved relevance.

    Vector search is good at semantic similarity but may not capture
    query-specific relevance. This node uses an LLM to re-score documents
    based on how well they answer the specific customer question.

    Re-ranking strategy:
    1. Score each document with LLM (0-1)
    2. Combine with original vector score: final = alpha * vector + (1-alpha) * llm
    3. Sort by final score and return top-N

    Args:
        state: Current workflow state with retrieved_docs and raw_message
        top_n: Number of documents to return after re-ranking
        alpha: Weight for combining scores (0=only LLM, 1=only vector)

    Returns:
        Dictionary with reranked_docs list
    """
    logger.info(f"Re-ranking documents for ticket: {state.get('ticket_id')}")

    retrieved_docs = state.get("retrieved_docs", [])
    if not retrieved_docs:
        logger.warning("No documents to re-rank")
        return {"reranked_docs": []}

    # Convert to RAGDocument objects
    rag_docs = [RAGDocument(**doc) for doc in retrieved_docs]

    llm = get_llm(temperature=0)
    structured_llm = llm.with_structured_output(RelevanceScore)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert at evaluating document relevance for customer support.

Score how relevant a knowledge base document is for answering a customer's question.

**Scoring Guidelines:**
- 1.0: Directly answers the question, highly relevant
- 0.7-0.9: Partially answers, related information
- 0.4-0.6: Tangentially related, some useful context
- 0.1-0.3: Minimally related, unlikely to help
- 0.0: Not relevant at all

Consider:
- Does it address the specific problem?
- Does it provide actionable steps?
- Is the information current and accurate?
- Would this help resolve the customer's issue?"""),
        ("human", """Customer Question: {question}

Document Title: {title}
Document Content: {content}

Rate the relevance of this document for answering the customer's question.""")
    ])

    chain = prompt | structured_llm

    reranked_docs = []

    try:
        # Score each document with LLM
        for i, doc in enumerate(rag_docs, 1):
            try:
                result = await chain.ainvoke({
                    "question": state["raw_message"],
                    "title": doc.title,
                    "content": doc.content[:500]  # Truncate for efficiency
                })

                # Create reranked document with combined score
                reranked = RerankedDocument.from_rag_document(
                    doc=doc,
                    rerank_score=result.relevance_score,
                    rank=i,  # Temporary rank, will be re-sorted
                    alpha=alpha
                )
                reranked_docs.append(reranked)

                logger.debug(
                    f"Doc {i}: {doc.doc_id} - "
                    f"Vector: {doc.score:.3f}, LLM: {result.relevance_score:.3f}, "
                    f"Final: {reranked.final_score:.3f}"
                )

            except Exception as e:
                logger.warning(f"Failed to re-rank document {doc.doc_id}: {e}")
                # Keep document with original score
                reranked_docs.append(
                    RerankedDocument.from_rag_document(
                        doc=doc,
                        rerank_score=doc.score,  # Use original score as fallback
                        rank=i,
                        alpha=1.0  # Full weight on original
                    )
                )

        # Sort by final score and update ranks
        reranked_docs.sort(key=lambda x: x.final_score, reverse=True)
        for i, doc in enumerate(reranked_docs, 1):
            doc.rank = i

        # Return top-N
        top_docs = reranked_docs[:top_n]

        logger.info(
            f"Re-ranked {len(reranked_docs)} documents, returning top {len(top_docs)}"
        )

        return {
            "reranked_docs": [doc.model_dump() for doc in top_docs]
        }

    except Exception as e:
        logger.error(f"Re-ranking failed: {e}")
        # Fallback: return top-N from original docs
        return {
            "reranked_docs": retrieved_docs[:top_n],
            "errors": [f"Re-ranking error: {str(e)}"]
        }
