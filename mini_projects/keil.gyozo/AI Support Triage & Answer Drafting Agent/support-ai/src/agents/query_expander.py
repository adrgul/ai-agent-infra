"""
Query expansion agent for SupportAI.

Generates semantic search queries for knowledge base retrieval.
"""

import json
from typing import List, Dict, Any

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from ..workflow.state import WorkflowState
from ..utils.config import settings
from ..utils.logger import get_logger
from ..templates.prompts import get_prompt_template

logger = get_logger(__name__)


async def expand_queries(state: WorkflowState) -> WorkflowState:
    """
    Generate semantic search queries for knowledge base retrieval.

    Args:
        state: Current workflow state

    Returns:
        Updated workflow state with search queries
    """
    try:
        logger.info(f"Expanding queries for ticket {state.get('ticket_id', 'unknown')}")

        # Get context from previous steps
        intent = state.get("intent", {})
        triage = state.get("triage", {})

        problem_type = intent.get("problem_type", "other")
        category = triage.get("category", "General Inquiry")

        # Initialize LLM
        llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0.3,  # Some creativity for query variation
            api_key=settings.openai_api_key
        )

        # Create prompt
        prompt = ChatPromptTemplate.from_template(get_prompt_template("query_expansion"))
        chain = prompt | llm

        # Generate queries
        ticket_text = state["original_message"]
        response = await chain.ainvoke({
            "ticket_text": ticket_text,
            "problem_type": problem_type,
            "category": category
        })

        # Parse JSON response
        try:
            queries = json.loads(response.content.strip())
            if not isinstance(queries, list):
                raise ValueError("Expected list of queries")
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse query expansion response: {e}")
            # Fallback to rule-based query generation
            queries = generate_fallback_queries(ticket_text, problem_type, category)

        # Validate and filter queries
        validated_queries = []
        for query in queries:
            if isinstance(query, str) and 3 <= len(query.split()) <= 10:
                validated_queries.append(query)
            if len(validated_queries) >= 5:  # Limit to 5 queries
                break

        # Ensure we have at least some queries
        if not validated_queries:
            validated_queries = generate_fallback_queries(ticket_text, problem_type, category)

        # Update state
        state["search_queries"] = validated_queries

        logger.info(f"Generated {len(validated_queries)} search queries: {validated_queries[:2]}...")

        return state

    except Exception as e:
        logger.error(f"Query expansion failed: {str(e)}")
        state["errors"].append(f"Query expansion error: {str(e)}")

        # Set fallback queries
        ticket_text = state.get("original_message", "")
        state["search_queries"] = generate_fallback_queries(ticket_text, "other", "General")

        return state


def generate_fallback_queries(ticket_text: str, problem_type: str, category: str) -> List[str]:
    """
    Generate fallback queries using rule-based approach.

    Args:
        ticket_text: Original ticket text
        problem_type: Problem type
        category: Category

    Returns:
        List of search queries
    """
    # Extract key terms from ticket (simple approach)
    words = ticket_text.lower().split()
    key_terms = [word for word in words if len(word) > 3][:5]  # Top 5 longer words

    # Problem type mappings
    type_queries = {
        "billing": ["billing issue", "payment problem", "invoice error", "charge dispute"],
        "technical": ["technical problem", "system error", "login issue", "feature not working"],
        "account": ["account access", "password reset", "profile update", "account settings"],
        "feature_request": ["new feature", "improvement request", "enhancement suggestion"],
        "other": ["general inquiry", "help needed", "support request"]
    }

    base_queries = type_queries.get(problem_type, type_queries["other"])

    # Combine with key terms
    queries = base_queries[:3]  # Start with base queries

    # Add term-specific queries
    for term in key_terms[:2]:  # Use top 2 key terms
        if term not in ["that", "this", "with", "from", "have", "been"]:
            queries.append(f"{term} issue")
            queries.append(f"{term} problem")

    # Ensure unique and reasonable length
    unique_queries = []
    seen = set()
    for query in queries:
        if query not in seen and 2 <= len(query.split()) <= 8:
            unique_queries.append(query)
            seen.add(query)

    return unique_queries[:5]  # Return top 5