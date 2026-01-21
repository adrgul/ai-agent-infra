"""
LangGraph state definition using TypedDict for proper dict-based state management.
"""
from typing import List, Dict, Any, Optional
from typing_extensions import TypedDict


class AgentState(TypedDict, total=False):
    """
    State model for the agent workflow.
    
    This is passed between nodes and accumulates data throughout execution.
    Using TypedDict ensures LangGraph handles state properly as a dict.
    """
    
    # User input
    user_input: str
    scenario: Optional[str]
    
    # Triage results
    classification: Optional[str]
    
    # Retrieval results
    retrieved_docs: List[str]
    retrieval_context: Optional[str]
    
    # Reasoning results
    reasoning_output: Optional[str]
    
    # Final output
    final_answer: Optional[str]
    
    # Metadata for observability
    nodes_executed: List[str]
    models_used: List[str]
    timings: Dict[str, float]
    cache_hits: Dict[str, bool]
