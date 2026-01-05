"""Query expansion node - generates search queries for RAG."""

import logging

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from ..models.state import SupportTicketState
from ..services import get_llm

logger = logging.getLogger(__name__)


class QueryExpansionResult(BaseModel):
    """Structured output for query expansion."""

    search_queries: list[str] = Field(
        ...,
        min_length=2,
        max_length=5,
        description="List of 2-5 search queries for knowledge base"
    )


async def query_expansion_node(state: SupportTicketState) -> dict:
    """Generate multiple search queries for RAG retrieval.

    Query expansion improves recall by reformulating the customer's question
    in different ways. This helps retrieve relevant documents even if they
    use different terminology.

    Strategies:
    - Rephrase using technical terms
    - Break down complex questions
    - Add category-specific keywords
    - Include synonyms and variations

    Args:
        state: Current workflow state with raw_message and category

    Returns:
        Dictionary with search_queries list
    """
    logger.info(f"Expanding queries for ticket: {state.get('ticket_id')}")

    llm = get_llm(temperature=0.3)  # Slightly higher temp for variation
    structured_llm = llm.with_structured_output(QueryExpansionResult)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert at formulating search queries for a knowledge base.

Your task is to generate 2-5 diverse search queries that will help find relevant
documentation to answer the customer's question.

**Guidelines:**
1. Use different phrasings and terminology
2. Include category-specific keywords (e.g., "billing", "payment", "subscription")
3. Break complex questions into simpler sub-questions
4. Use both customer language and technical terms
5. Keep queries concise and specific (5-15 words each)

**Examples:**
Customer: "I was charged twice for my subscription"
Queries:
- duplicate subscription charge resolution
- how to handle double billing
- refund process for duplicate payment
- subscription billing error troubleshooting

Customer: "My dashboard won't load"
Queries:
- dashboard loading issues
- troubleshoot dashboard errors
- fix dashboard not displaying
- dashboard performance problems"""),
        ("human", """Category: {category}
Customer Message: {message}

Generate 2-5 search queries to find relevant knowledge base articles.""")
    ])

    chain = prompt | structured_llm

    try:
        result = await chain.ainvoke({
            "category": state.get("category", "General"),
            "message": state["raw_message"]
        })

        logger.info(f"Generated {len(result.search_queries)} search queries")
        for i, query in enumerate(result.search_queries, 1):
            logger.debug(f"  Query {i}: {query}")

        return {
            "search_queries": result.search_queries
        }

    except Exception as e:
        logger.error(f"Query expansion failed: {e}")
        # Fallback: use original message as single query
        return {
            "search_queries": [state["raw_message"][:100]],
            "errors": [f"Query expansion error: {str(e)}"]
        }
