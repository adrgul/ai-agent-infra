from datetime import datetime
from typing import List

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import END, StateGraph

from ..models.schemas import MessageRecord
from ..models.state import AgentState
from .llm_client import LLMClient


class AgentOrchestrator:
    """LangGraph-based orchestrator for the chat agent (web search removed)."""

    def __init__(
        self,
        llm_client: LLMClient | None = None,
    ) -> None:
        self.llm = llm_client or LLMClient()
        graph = StateGraph(AgentState)
        graph.add_node("build_prompt", self.build_prompt)
        graph.add_node("call_llm", self.call_llm)
        graph.set_entry_point("build_prompt")
        graph.add_edge("build_prompt", "call_llm")
        graph.add_edge("call_llm", END)
        self.workflow = graph.compile()

    def maybe_search(self, state: AgentState) -> AgentState:
        """Deprecated: web search was removed."""
        state["rag_context"] = state.get("rag_context") or []
        return state

    async def run(self, initial_state: AgentState) -> AgentState:
        return await self.workflow.ainvoke(initial_state)

    def maybe_search(self, state: AgentState) -> AgentState:
        allow_search = state.get("enable_search", True)
        if allow_search and self.search.enabled:
            state["rag_context"] = self.search.search(state.get("query", ""))
        else:
            state["rag_context"] = state.get("rag_context") or []
        return state

    def build_prompt(self, state: AgentState) -> AgentState:
        rag_context = state.get("rag_context") or []
        history = state.get("history") or []
        history_text = self._history_to_text(history)
        system_prompt = (
            "You are KnowledgeRouter, a helpful internal assistant. "
            "If search context is provided, use it directly and do not claim you cannot search. "
            "If no search context is available, answer from your general knowledge without apologizing."
        )
        user_prompt = (
            f"User question at {datetime.utcnow().isoformat()}:\n"
            f"{state.get('query','')}\n\n"
            f"Conversation history:\n{history_text if history_text else 'None'}\n\n"
            f"Search / RAG context:\n{rag_context if rag_context else 'None'}\n\n"
            "Compose a concise, actionable answer. If context is present, ground the answer in it."
        )
        state["system_prompt"] = system_prompt
        state["final_prompt"] = user_prompt
        state["history_messages"] = self._history_to_messages(history)
        return state

    async def call_llm(self, state: AgentState) -> AgentState:
        response_text = await self.llm.generate(
            system_prompt=state.get("system_prompt", "You are KnowledgeRouter."),
            user_prompt=state.get("final_prompt", ""),
            history=state.get("history_messages") or [],
        )
        state["response_text"] = response_text
        return state

    def _history_to_messages(self, history: List[MessageRecord]):
        messages = []
        for item in history:
            if item.role == "assistant":
                messages.append(AIMessage(content=item.content))
            else:
                messages.append(HumanMessage(content=item.content))
        return messages

    def _history_to_text(self, history: List[MessageRecord]) -> str:
        lines = []
        for msg in history:
            lines.append(f"{msg.role}: {msg.content}")
        return "\n".join(lines)
