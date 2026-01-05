"""LangGraph state models.

CRITICAL: Node names must NOT collide with state field names!
Convention: State fields use nouns, node names use verb_noun pattern.
"""

from typing import Optional, TypedDict


class SupportTicketState(TypedDict, total=False):
    """State object for support ticket processing workflow.

    ⚠️ NAMING RULE: All fields here are NOUNS. Node names must use VERB_NOUN pattern!
    Example: State field 'policy_check' → Node name 'check_policy'
    """

    # Input fields
    ticket_id: str
    raw_message: str
    customer_name: str
    customer_email: str

    # Intent Detection (node: detect_intent)
    problem_type: str  # billing | technical | account | feature_request
    sentiment: str     # frustrated | neutral | satisfied

    # Triage (node: triage_classify)
    category: str
    subcategory: str
    priority: str      # P1 | P2 | P3
    sla_hours: int
    suggested_team: str
    triage_confidence: float

    # RAG (nodes: expand_queries, search_rag, rerank_docs)
    search_queries: list[str]
    retrieved_docs: list[dict]
    reranked_docs: list[dict]

    # Draft (node: draft_answer)
    answer_draft: dict
    citations: list[dict]

    # Validation (nodes: check_policy, validate_output)
    policy_check: dict   # ⚠️ Node must be named "check_policy" to avoid collision!
    output: dict

    # Metadata
    processed_at: Optional[str]
    errors: Optional[list[str]]
