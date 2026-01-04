from typing import Dict, List, TypedDict

from .schemas import MessageRecord


class AgentState(TypedDict, total=False):
    user_id: str
    session_id: str
    query: str
    history: List[MessageRecord]
    history_messages: List
    rag_context: List[str]
    final_prompt: str
    response_text: str
    request_metadata: Dict
    enable_search: bool
