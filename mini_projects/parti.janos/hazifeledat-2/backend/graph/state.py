from typing import TypedDict, List, Optional, Any, Dict
from langchain_core.messages import BaseMessage
from domain.models import Citation

class AgentState(TypedDict):
    input: str
    chat_history: List[BaseMessage]
    domain: Optional[str]
    intent: Optional[str] # "query" or "action"
    tool_name: Optional[str]
    tool_args: Optional[Dict[str, Any]]
    retrieved_docs: List[Any]
    citations: List[Citation]  # Document citations with scores
    final_response: Optional[str]
