"""LangGraph workflow orchestration for support ticket processing.

⚠️ CRITICAL NAMING CONVENTION:
Node names use verb_noun pattern to avoid collision with state fields!
- State field: policy_check (noun)
- Node name: check_policy (verb_noun)

This prevents the runtime error: "'X' is already being used as a state key"
"""

import logging
from typing import Optional

from langgraph.graph import StateGraph, END

from ..models.state import SupportTicketState
from ..nodes import (
    intent_detection_node,
    triage_classify_node,
    query_expansion_node,
    rag_search_node,
    rerank_node,
    draft_answer_node,
    policy_check_node,
    validation_node
)
from ..services import QdrantService, EmbeddingService

logger = logging.getLogger(__name__)


def build_support_workflow(
    qdrant_service: Optional[QdrantService] = None,
    embedding_service: Optional[EmbeddingService] = None
) -> StateGraph:
    """Build the LangGraph workflow for support ticket processing.

    Workflow sequence:
    1. detect_intent: Classify problem type and sentiment
    2. triage_classify: Assign category, priority, SLA, team
    3. expand_queries: Generate multiple search queries
    4. search_rag: Vector search in Qdrant
    5. rerank_docs: Re-rank documents with LLM
    6. draft_answer: Generate response with citations
    7. check_policy: Validate business rules compliance
    8. validate_output: Format final JSON output

    Args:
        qdrant_service: Optional Qdrant service instance (for dependency injection)
        embedding_service: Optional embedding service instance

    Returns:
        Compiled StateGraph ready for execution
    """
    logger.info("Building support ticket workflow")

    # Initialize workflow with state schema
    workflow = StateGraph(SupportTicketState)

    # Add nodes - NOTE: Using verb prefixes to avoid state field collisions!
    logger.debug("Adding workflow nodes")

    workflow.add_node("detect_intent", intent_detection_node)
    workflow.add_node("triage_classify", triage_classify_node)
    workflow.add_node("expand_queries", query_expansion_node)

    # RAG search node with dependency injection
    async def rag_search_with_services(state: SupportTicketState) -> dict:
        """Wrapper to inject services into rag_search_node."""
        return await rag_search_node(
            state,
            qdrant_service=qdrant_service,
            embedding_service=embedding_service
        )

    workflow.add_node("search_rag", rag_search_with_services)
    workflow.add_node("rerank_docs", rerank_node)
    workflow.add_node("draft_answer", draft_answer_node)

    # ⚠️ CRITICAL: Node name "check_policy" != state field "policy_check"
    workflow.add_node("check_policy", policy_check_node)

    workflow.add_node("validate_output", validation_node)

    # Define workflow edges (linear flow)
    logger.debug("Defining workflow edges")

    workflow.set_entry_point("detect_intent")
    workflow.add_edge("detect_intent", "triage_classify")
    workflow.add_edge("triage_classify", "expand_queries")
    workflow.add_edge("expand_queries", "search_rag")
    workflow.add_edge("search_rag", "rerank_docs")
    workflow.add_edge("rerank_docs", "draft_answer")
    workflow.add_edge("draft_answer", "check_policy")  # ⚠️ Using correct node name
    workflow.add_edge("check_policy", "validate_output")
    workflow.add_edge("validate_output", END)

    # Compile workflow
    logger.debug("Compiling workflow")
    compiled_workflow = workflow.compile()

    logger.info("Support ticket workflow built successfully")

    return compiled_workflow


def verify_node_names(workflow_graph: StateGraph) -> None:
    """Verify that node names don't collide with state field names.

    This helper function can be used during development to catch
    naming collisions before runtime.

    Args:
        workflow_graph: The workflow graph to verify

    Raises:
        ValueError: If any node name conflicts with a state field
    """
    state_fields = set(SupportTicketState.__annotations__.keys())
    node_names = set(workflow_graph.nodes.keys())

    conflicts = state_fields.intersection(node_names)

    if conflicts:
        raise ValueError(
            f"Node names conflict with state fields: {conflicts}\n"
            f"Use verb_noun pattern for nodes (e.g., 'check_policy' instead of 'policy_check')"
        )

    logger.info("Node naming verification passed - no conflicts found")
