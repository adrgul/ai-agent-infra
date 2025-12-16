"""
Services - LangGraph-based agent orchestration.
"""
import json
import logging
from typing import Dict, Any, Sequence, Annotated
from typing_extensions import TypedDict

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

from domain.models import DomainType, QueryResponse, Citation, Memory, Message

logger = logging.getLogger(__name__)


class AgentState(TypedDict, total=False):
    """LangGraph state object."""
    messages: Sequence[BaseMessage]
    query: str
    domain: str
    retrieved_docs: list
    output: Dict[str, Any]
    citations: list
    workflow: Dict[str, Any]
    user_id: str


class QueryAgent:
    """Multi-domain RAG + Workflow agent using LangGraph."""

    def __init__(self, llm_client: ChatOpenAI, rag_client):
        self.llm = llm_client
        self.rag_client = rag_client
        self.workflow = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build LangGraph workflow."""
        graph = StateGraph(AgentState)

        # Add nodes
        graph.add_node("intent_detection", self._intent_detection_node)
        graph.add_node("retrieval", self._retrieval_node)
        graph.add_node("generation", self._generation_node)
        graph.add_node("execute_workflow", self._workflow_node)

        # Set entry point
        graph.set_entry_point("intent_detection")

        # Add edges
        graph.add_edge("intent_detection", "retrieval")
        graph.add_edge("retrieval", "generation")
        graph.add_edge("generation", "execute_workflow")
        graph.add_edge("execute_workflow", END)

        return graph.compile()

    async def _intent_detection_node(self, state: AgentState) -> AgentState:
        """Detect which domain this query belongs to."""
        logger.info("Intent detection node executing")

        prompt = f"""
Classify the following query into ONE domain:
- hr (human resources, vacation, benefits, hiring)
- it (tech support, VPN, access, software)
- finance (invoices, expenses, budgets, payments)
- legal (contracts, compliance, policies)
- marketing (brand, campaigns, content)
- general (other queries)

Query: "{state['query']}"

Respond with ONLY the domain name (lowercase).
"""
        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        domain = response.content.strip().lower()

        # Validate domain
        try:
            DomainType(domain)
        except ValueError:
            domain = DomainType.GENERAL.value

        state["domain"] = domain
        state["messages"] = [HumanMessage(content=state["query"])]
        logger.info(f"Detected domain: {domain}")

        return state

    async def _retrieval_node(self, state: AgentState) -> AgentState:
        """Retrieve relevant documents from RAG."""
        logger.info(f"Retrieval node executing for domain={state['domain']}")

        citations = await self.rag_client.retrieve_for_domain(
            domain=state["domain"],
            query=state["query"],
            top_k=5
        )

        state["citations"] = [c.model_dump() for c in citations]
        state["retrieved_docs"] = citations
        logger.info(f"Retrieved {len(citations)} documents")

        return state

    async def _generation_node(self, state: AgentState) -> AgentState:
        """Generate response using RAG context."""
        logger.info("Generation node executing")

        # Build context from citations with content
        context_parts = []
        for c in state["citations"]:
            # If chunk content is available, use it; otherwise just show title
            if c.get("content"):
                context_parts.append(f"[{c['doc_id']}] {c['title']}\n{c['content'][:500]}...")
            else:
                context_parts.append(f"[{c['doc_id']}] {c['title']}")
        
        context = "\n\n".join(context_parts)

        prompt = f"""
You are a helpful HR/IT/Finance/Legal/Marketing assistant.

Retrieved documents:
{context}

User query: "{state['query']}"

Provide a helpful answer based on the retrieved documents.
If the documents don't contain relevant information, say so clearly.
Answer in Hungarian if the query is in Hungarian, otherwise in English.
"""

        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        answer = response.content

        state["output"] = {
            "domain": state["domain"],
            "answer": answer,
            "citations": state["citations"],
        }

        state["messages"].append(AIMessage(content=answer))
        logger.info("Generation completed")

        return state

    async def _workflow_node(self, state: AgentState) -> AgentState:
        """Execute domain-specific workflows if needed."""
        logger.info(f"Workflow node executing for domain={state['domain']}")

        domain = state.get("domain", "general")

        if domain == DomainType.HR.value:
            # Example: HR vacation request workflow
            query_lower = state["query"].lower()
            if any(kw in query_lower for kw in ["szabadság", "szabadsag", "vacation", "szabis"]):
                state["workflow"] = {
                    "action": "hr_request_draft",
                    "type": "vacation_request",
                    "status": "draft",
                    "next_step": "Review and submit"
                }
        elif domain == DomainType.IT.value:
            # Example: IT support ticket workflow
            if any(kw in state["query"].lower() for kw in ["nem működik", "error", "problem"]):
                state["workflow"] = {
                    "action": "it_ticket_draft",
                    "type": "support_ticket",
                    "priority": "medium",
                    "next_step": "Submit to Jira"
                }

        return state

    async def run(self, query: str, user_id: str, session_id: str) -> QueryResponse:
        """Execute agent workflow."""
        logger.info(f"Agent run: user={user_id}, session={session_id}, query={query[:50]}...")

        initial_state: AgentState = {
            "query": query,
            "user_id": user_id,
            "messages": [],
            "domain": "",
            "retrieved_docs": [],
            "citations": [],
            "workflow": None,
        }

        final_state = await self.workflow.ainvoke(initial_state)

        # Build response
        response = QueryResponse(
            domain=final_state["domain"],
            answer=final_state["output"]["answer"],
            citations=[Citation(**c) for c in final_state["citations"]],
            workflow=final_state.get("workflow"),
        )

        logger.info("Agent run completed")
        return response
