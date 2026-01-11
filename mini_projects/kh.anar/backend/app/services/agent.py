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
        rag_service=None,
    ) -> None:
        self.llm = llm_client or LLMClient()
        # RAG service is injected to keep OCP/DIP and for easy testing
        self.rag = rag_service
        graph = StateGraph(AgentState)
        # KB-first routing: route_query -> build_prompt -> call_llm
        graph.add_node("route_query", self.route_query)
        graph.add_node("build_prompt", self.build_prompt)
        graph.add_node("call_llm", self.call_llm)
        graph.set_entry_point("route_query")
        graph.add_edge("route_query", "build_prompt")
        graph.add_edge("build_prompt", "call_llm")
        graph.add_edge("call_llm", END)
        self.workflow = graph.compile()

    def maybe_search(self, state: AgentState) -> AgentState:
        """Deprecated: web search was removed."""
        state["rag_context"] = state.get("rag_context") or []
        return state

    async def run(self, initial_state: AgentState) -> AgentState:
        return await self.workflow.ainvoke(initial_state)

    def route_query(self, state: AgentState) -> AgentState:
        """KB-first routing: use the injected RAG service to get context.

        If RAG returns 'no_hit', we leave rag_context empty and annotate the
        state for potential fallback. This ensures the downstream prompt will
        be KB-first: it receives context when available and otherwise nothing.
        """
        state["rag_context"] = []
        if not self.rag:
            # no RAG service injected -> noop
            return state
        q = state.get("query", "")
        # RBAC: if the user has a scope in preferences, pass it as a filter
        prefs = state.get("request_metadata", {}) or {}
        access_scope = prefs.get("access_scope") or (state.get("user_preferences", {}).get("access_scope") if state.get("user_preferences") else None)
        filters = {**(prefs), **({"access_scope": access_scope} if access_scope else {})}
        # ChromaDB requires None for no filters, not empty dict
        if not filters:
            filters = None
        telemetry = self.rag.route_and_retrieve(q, filters=filters)
        state["rag_telemetry"] = telemetry
        if telemetry.get("decision") == "hit":
            # include topk hits as context for the prompt generation
            state["rag_context"] = telemetry.get("topk", [])
        else:
            state["rag_context"] = []
            state["rag_telemetry"]["fallback_reason"] = "no_hit_or_low_confidence"
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
