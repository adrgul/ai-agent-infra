"""
Workflow state definition for LangGraph.

TypedDict defining the state passed between workflow nodes.
"""

from typing import Dict, List, Optional, Any, TypedDict


class WorkflowState(TypedDict, total=False):
    """State dictionary for the SupportAI LangGraph workflow."""

    # Input data
    ticket_id: str
    original_message: str
    customer_email: Optional[str]
    subject: Optional[str]
    channel: Optional[str]

    # Processing results
    intent: Optional[Dict[str, Any]]  # From intent detection
    triage: Optional[Dict[str, Any]]  # From triage classification
    search_queries: Optional[List[str]]  # From query expansion
    retrieved_docs: Optional[List[Dict[str, Any]]]  # From vector search
    reranked_docs: Optional[List[Dict[str, Any]]]  # From re-ranking
    draft: Optional[Dict[str, Any]]  # From draft generation
    policy_check: Optional[Dict[str, Any]]  # From policy checking

    # Final output
    final_output: Optional[Dict[str, Any]]  # Complete structured output

    # Error tracking
    errors: List[str]

    # Metadata
    processing_start_time: Optional[float]
    node_execution_times: Optional[Dict[str, float]]