"""
Services - LangGraph-based agent orchestration.
"""
import logging
import re
from typing import Dict, Any, Sequence
from typing_extensions import TypedDict

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

from domain.models import DomainType, QueryResponse, Citation
from infrastructure.error_handling import check_token_limit, estimate_tokens
from infrastructure.atlassian_client import atlassian_client

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
    # Telemetry fields
    rag_context: str  # Full RAG context sent to LLM
    llm_prompt: str   # Complete prompt sent to LLM
    llm_response: str # Raw LLM response


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

        # Simple keyword-based pre-classification for better accuracy
        query_lower = state['query'].lower()
        
        # Explicit marketing keywords (expanded with variations)
        marketing_keywords = [
            'brand', 'logo', 'color', 'font', 'typography', 'design', 'layout', 
            'arculat', 'guideline', 'betűtípus', 'betutipus', 'sorhossz', 'színek', 
            'szinek', 'márka', 'marka', 'spacing', 'térköz', 'terkoz', 'elrendezés', 
            'elrendezes', 'margin', 'tipográfia', 'tipografia', 'visual', 'vizuális',
            'vizualis', 'ikonográfia', 'ikonografia'
        ]
        if any(kw in query_lower for kw in marketing_keywords):
            domain = DomainType.MARKETING.value
            state["domain"] = domain
            state["messages"] = [HumanMessage(content=state["query"])]
            logger.info(f"Detected domain (keyword match): {domain}")
            return state
        
        # Otherwise use LLM
        prompt = f"""
Classify this query into ONE category:

marketing = brand, logo, visual-design, arculat, guideline
hr = vacation, employee, szabadság
it = VPN, computer, software
finance = invoice, expense, számla
legal = contract, szerződés
general = other

Query: "{state['query']}"

Category:"""
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
        
        # Build RAG context for telemetry (use section_id for IT domain)
        is_it_domain = state.get("domain") == DomainType.IT.value
        context_parts = []
        for i, c in enumerate(citations, 1):
            if hasattr(c, 'content') and c.content:
                # For IT domain, use section_id if available
                if is_it_domain:
                    section_id = c.section_id if hasattr(c, 'section_id') else None
                    if not section_id and c.content:
                        match = re.search(r"\[([A-Z]+-KB-\d+)\]", c.content)
                        section_id = match.group(1) if match else None
                    doc_label = f"[{section_id}]" if section_id else f"[Doc {i}: {c.title}]"
                else:
                    doc_label = f"[Doc {i}: {c.title}]"
                context_parts.append(f"{doc_label}\n{c.content[:500]}...")
            else:
                context_parts.append(f"[Doc {i}: {c.title}]")
        state["rag_context"] = "\n\n".join(context_parts)
        
        logger.info(f"Retrieved {len(citations)} documents")

        return state

    async def _generation_node(self, state: AgentState) -> AgentState:
        """Generate response using RAG context with token limit protection."""
        logger.info("Generation node executing")

        # Build context from citations with content
        context_parts = []
        is_it_domain = state.get("domain") == DomainType.IT.value
        
        for i, c in enumerate(state["citations"], 1):
            # If chunk content is available, use it
            if c.get("content"):
                # For IT domain, try to use section_id; fallback to IT Policy label to avoid "Document X"
                if is_it_domain:
                    section_id = c.get("section_id")
                    if not section_id:
                        match = re.search(r"([A-Z]+-KB-\d+)", c["content"])
                        section_id = match.group(1) if match else None
                    doc_label = f"[{section_id}]" if section_id else "[IT Policy]"
                    c["section_id"] = section_id  # propagate inferred id for later use
                else:
                    doc_label = f"[Document {i}: {c['title']}]"
                
                # Use full content for top 3 results, truncate rest to avoid timeout
                if i <= 3:
                    context_parts.append(f"{doc_label}\n{c['content']}")
                else:
                    context_parts.append(f"{doc_label}\n{c['content'][:300]}...")
            else:
                context_parts.append(f"[Document {i}: {c['title']}]")
        
        context = "\n\n".join(context_parts)

        # Domain-specific instructions
        domain_instructions = ""
        if state.get("domain") == DomainType.IT.value:
            domain_instructions = """
IMPORTANT FOR IT QUESTIONS:
1. Provide clear, step-by-step troubleshooting or guidance based on the retrieved IT Policy documents
2. **ALWAYS reference the exact section IDs** when cited (e.g., [IT-KB-234], [IT-KB-320])
   - Use the exact format shown in square brackets at the start of each document (e.g., [IT-KB-267])
   - Example: "A VPN hibaelhárítási folyamat [IT-KB-267] alapján először ellenőrizd..."
   - Do NOT use [Document 1], [Document 2] format - use the actual section IDs
3. Include procedures and responsible parties if mentioned in the documents
4. At the end of your response, ALWAYS ask if the user wants to create a Jira support ticket

Format your offer like this:
"📋 Szeretnéd, hogy létrehozzak egy Jira support ticketet ehhez a kérdéshez? (Válaszolj 'igen'-nel vagy 'nem'-mel)"

This question MUST appear at the end of EVERY IT domain response.
"""

        prompt = f"""
You are a helpful HR/IT/Finance/Legal/Marketing assistant.

Retrieved documents (use ALL relevant information):
{context}

User query: "{state['query']}"

{domain_instructions}

Provide a comprehensive answer based on the retrieved documents above.
Combine information from multiple sources when they relate to the same topic.
If asking about guidelines or rules, include ALL relevant details found in the documents.
Use proper formatting with line breaks and bullet points for better readability.
Answer in Hungarian if the query is in Hungarian, otherwise in English.
"""

        # Check token limit before sending to OpenAI
        try:
            check_token_limit(prompt, max_tokens=100000)  # gpt-4o-mini 128k context
            logger.info(f"Prompt size: ~{estimate_tokens(prompt)} tokens")
        except ValueError as e:
            logger.error(f"Token limit exceeded: {e}")
            # Truncate context and retry
            context_parts = context_parts[:3]  # Only use top 3 docs
            context = "\n\n".join(context_parts)
            prompt = f"""
You are a helpful HR/IT/Finance/Legal/Marketing assistant.

Retrieved documents:
{context}

User query: "{state['query']}"

Provide an answer based on the retrieved documents above.
Answer in Hungarian if the query is in Hungarian, otherwise in English.
"""
            logger.warning("Prompt truncated to fit token limit")

        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        answer = response.content

        # Ensure IT answers surface section references even if the model forgets
        if is_it_domain:
            section_ids = []
            for citation in state.get("citations", []):
                section_id = citation.get("section_id")
                if not section_id and citation.get("content"):
                    match = re.search(r"([A-Z]+-KB-\d+)", citation["content"])
                    section_id = match.group(1) if match else None
                    citation["section_id"] = section_id
                if section_id and section_id not in section_ids:
                    section_ids.append(section_id)

            if section_ids and not any(sid in answer for sid in section_ids):
                refs = ", ".join(f"[{sid}]" for sid in section_ids)
                answer = f"{answer}\n\nForrás: {refs} – IT Üzemeltetési és Felhasználói Szabályzat"
        
        # Save telemetry data
        state["llm_prompt"] = prompt
        state["llm_response"] = answer

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
            # IT domain: Offer Jira ticket creation
            # (Citations already retrieved from Qdrant by _retrieval_node)
            logger.info("🔧 IT workflow: Setting up Jira ticket creation offer")
            
            state["workflow"] = {
                "action": "it_support_ready",
                "type": "it_support",
                "next_step": "Offer Jira ticket creation",
                "jira_available": True
            }

        return state

    async def regenerate(self, query: str, domain: str, citations: list, user_id: str) -> QueryResponse:
        """Regenerate response using cached domain + citations (skip intent + RAG)."""
        logger.info(f"Agent regenerate: user={user_id}, domain={domain}, cached_citations={len(citations)}")

        # Build state with cached data
        initial_state: AgentState = {
            "query": query,
            "user_id": user_id,
            "messages": [HumanMessage(content=query)],
            "domain": domain,  # ← FROM CACHE
            "citations": citations,  # ← FROM CACHE
            "retrieved_docs": [],
            "workflow": None,
        }

        # SKIP intent detection node
        # SKIP retrieval node
        # Run ONLY generation + workflow
        logger.info("Skipping intent detection and RAG retrieval (using cache)")
        
        state_after_generation = await self._generation_node(initial_state)
        final_state = await self._workflow_node(state_after_generation)

        # Build response
        response = QueryResponse(
            domain=final_state["domain"],
            answer=final_state["output"]["answer"],
            citations=[Citation(**c) for c in final_state["citations"]],
            workflow=final_state.get("workflow"),
        )

        logger.info("Agent regenerate completed (cached)")
        return response

    async def run(self, query: str, user_id: str, session_id: str) -> QueryResponse:
        """Execute full agent workflow (all 4 nodes)."""
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

        # Build response with telemetry
        response = QueryResponse(
            domain=final_state["domain"],
            answer=final_state["output"]["answer"],
            citations=[Citation(**c) for c in final_state["citations"]],
            workflow=final_state.get("workflow"),
            rag_context=final_state.get("rag_context"),
            llm_prompt=final_state.get("llm_prompt"),
            llm_response=final_state.get("llm_response"),
        )

        logger.info("Agent run completed")
        return response
