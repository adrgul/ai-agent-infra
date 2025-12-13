"""
LangGraph workflow for SupportAI.

Orchestrates the complete support ticket processing pipeline.
"""

from typing import Dict, Any, List
import asyncio

from langgraph.graph import StateGraph, END

from ..workflow.state import WorkflowState
from ..agents.intent_detector import detect_intent
from ..agents.triage_classifier import classify_triage
from ..agents.query_expander import expand_queries
from ..agents.draft_generator import generate_draft
from ..agents.policy_checker import check_policies
from ..retrieval.vector_store import vector_store
from ..retrieval.embeddings import embedding_service
from ..retrieval.reranker import reranker
from ..schemas.output_schema import SupportAgentOutput
from ..utils.logger import get_logger
from ..utils.validators import validate_output

logger = get_logger(__name__)


async def vector_search_node(state: WorkflowState) -> WorkflowState:
    """Vector search node for knowledge base retrieval."""
    try:
        logger.info("Performing vector search")

        queries = state.get("search_queries", [])
        if not queries:
            logger.warning("No search queries available")
            state["retrieved_docs"] = []
            return state

        # Use the first query for now (could be enhanced to combine results)
        query = queries[0]

        # Generate embedding for query
        query_embedding = await embedding_service.embed_query(query)

        # Search vector store
        # Note: This is a simplified implementation
        # In practice, you'd need to implement the search method properly
        retrieved_docs = vector_store.search(query, top_k=10)

        # Convert to expected format
        formatted_docs = []
        for doc in retrieved_docs:
            formatted_docs.append({
                "doc_id": doc.doc_id,
                "title": doc.metadata.get("title", "Untitled"),
                "content": doc.content,
                "score": 0.8,  # Placeholder score
                "url": doc.metadata.get("url", ""),
                "category": doc.metadata.get("category", "")
            })

        state["retrieved_docs"] = formatted_docs
        logger.info(f"Retrieved {len(formatted_docs)} documents")

        return state

    except Exception as e:
        logger.error(f"Vector search failed: {str(e)}")
        state["errors"].append(f"Vector search error: {str(e)}")
        state["retrieved_docs"] = []
        return state


async def rerank_node(state: WorkflowState) -> WorkflowState:
    """Document re-ranking node."""
    try:
        logger.info("Re-ranking documents")

        retrieved_docs = state.get("retrieved_docs", [])
        search_queries = state.get("search_queries", [])

        if not retrieved_docs or not search_queries:
            state["reranked_docs"] = retrieved_docs
            return state

        # Use first query for re-ranking
        query = search_queries[0]

        # Re-rank documents
        reranked_docs = await reranker.rerank(query, retrieved_docs, top_k=3)

        state["reranked_docs"] = reranked_docs
        logger.info(f"Re-ranked to {len(reranked_docs)} top documents")

        return state

    except Exception as e:
        logger.error(f"Re-ranking failed: {str(e)}")
        state["errors"].append(f"Re-ranking error: {str(e)}")
        state["reranked_docs"] = state.get("retrieved_docs", [])
        return state


async def validate_output_node(state: WorkflowState) -> WorkflowState:
    """Final output validation and formatting."""
    try:
        logger.info("Validating final output")

        # Gather all components
        triage = state.get("triage", {})
        draft = state.get("draft", {})
        citations = state.get("citations", [])
        policy_check = state.get("policy_check", {})

        # Create final output
        final_output = {
            "ticket_id": state.get("ticket_id", "unknown"),
            "timestamp": state.get("timestamp"),
            "triage": triage,
            "answer_draft": draft,
            "citations": citations,
            "policy_check": policy_check
        }

        # Validate against schema
        try:
            validated_output = SupportAgentOutput(**final_output)
            state["final_output"] = validated_output.model_dump()
            logger.info("Output validation successful")
        except Exception as e:
            logger.error(f"Output validation failed: {str(e)}")
            state["errors"].append(f"Output validation error: {str(e)}")
            # Still set the output, but mark as invalid
            state["final_output"] = final_output

        return state

    except Exception as e:
        logger.error(f"Output validation failed: {str(e)}")
        state["errors"].append(f"Output validation error: {str(e)}")
        return state


def should_escalate(state: WorkflowState) -> str:
    """
    Determine if ticket should be escalated to human review.

    Args:
        state: Current workflow state

    Returns:
        Next node: "validate_output" or END
    """
    policy_check = state.get("policy_check", {})
    errors = state.get("errors", [])

    # Escalate if policy check failed
    if policy_check.get("compliance") == "failed":
        logger.info("Escalating due to policy violation")
        return END

    # Escalate if there were critical errors
    if errors:
        logger.info(f"Escalating due to {len(errors)} errors")
        return END

    # Escalate if confidence is too low
    triage = state.get("triage", {})
    if triage.get("confidence", 1.0) < 0.5:
        logger.info("Escalating due to low confidence")
        return END

    # Proceed to validation
    return "validate_output"


def create_support_workflow() -> StateGraph:
    """
    Create the complete LangGraph workflow for support ticket processing.

    Returns:
        Compiled StateGraph workflow
    """
    workflow = StateGraph(WorkflowState)

    # Add nodes
    workflow.add_node("detect_intent", detect_intent)
    workflow.add_node("classify_triage", classify_triage)
    workflow.add_node("expand_queries", expand_queries)
    workflow.add_node("vector_search", vector_search_node)
    workflow.add_node("rerank", rerank_node)
    workflow.add_node("generate_draft", generate_draft)
    workflow.add_node("check_policy", check_policies)
    workflow.add_node("validate_output", validate_output_node)

    # Define the workflow edges
    workflow.set_entry_point("detect_intent")

    # Sequential flow
    workflow.add_edge("detect_intent", "classify_triage")
    workflow.add_edge("classify_triage", "expand_queries")
    workflow.add_edge("expand_queries", "vector_search")
    workflow.add_edge("vector_search", "rerank")
    workflow.add_edge("rerank", "generate_draft")
    workflow.add_edge("generate_draft", "check_policy")

    # Conditional edge based on policy check
    workflow.add_conditional_edges(
        "check_policy",
        should_escalate,
        {
            "validate_output": "validate_output",
            END: END  # Escalate to human
        }
    )

    workflow.add_edge("validate_output", END)

    logger.info("SupportAI workflow created successfully")

    return workflow.compile()


# Global workflow instance
support_workflow = create_support_workflow()