"""
LangGraph agent workflow definition.
Orchestrates the triage → retrieval/reasoning → summary flow.
"""
import logging
from typing import Literal, Dict
from langgraph.graph import StateGraph, END
from app.graph.state import AgentState
from app.nodes.triage_node import TriageNode
from app.nodes.retrieval_node import RetrievalNode
from app.nodes.reasoning_node import ReasoningNode
from app.nodes.summary_node import SummaryNode
from app.llm.interfaces import LLMClient
from app.llm.models import ModelSelector
from app.llm.cost_tracker import CostTracker
from app.cache.interfaces import Cache

logger = logging.getLogger(__name__)


class AgentGraphFactory:
    """
    Factory for creating the agent workflow graph.
    
    Follows Dependency Inversion Principle:
    - Accepts interfaces, not concrete implementations
    - Nodes are composed via constructor injection
    
    This is the "composition root" where dependencies are wired together.
    """
    
    def __init__(
        self,
        llm_client: LLMClient,
        model_selector: ModelSelector,
        cost_tracker: CostTracker,
        node_cache: Cache,
        embedding_cache: Cache
    ):
        """
        Initialize graph factory with dependencies.
        
        Args:
            llm_client: LLM client interface
            model_selector: Model selection service
            cost_tracker: Cost tracking service
            node_cache: Cache for node-level caching
            embedding_cache: Cache for embeddings
        """
        self.llm_client = llm_client
        self.model_selector = model_selector
        self.cost_tracker = cost_tracker
        self.node_cache = node_cache
        self.embedding_cache = embedding_cache
    
    def create_graph(self):
        """
        Create and compile the LangGraph workflow.
        
        Graph structure:
        START → triage → conditional_route → retrieval/reasoning/summary → summary → END
        
        Returns:
            Compiled LangGraph
        """
        # Create node instances with dependency injection
        triage_node = TriageNode(
            llm_client=self.llm_client,
            cost_tracker=self.cost_tracker,
            model_selector=self.model_selector,
            cache=self.node_cache
        )
        
        retrieval_node = RetrievalNode(
            llm_client=self.llm_client,
            cost_tracker=self.cost_tracker,
            model_selector=self.model_selector,
            embedding_cache=self.embedding_cache
        )
        
        reasoning_node = ReasoningNode(
            llm_client=self.llm_client,
            cost_tracker=self.cost_tracker,
            model_selector=self.model_selector
        )
        
        summary_node = SummaryNode(
            llm_client=self.llm_client,
            cost_tracker=self.cost_tracker,
            model_selector=self.model_selector
        )
        
        # Build graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("triage", triage_node.execute)
        workflow.add_node("retrieval", retrieval_node.execute)
        workflow.add_node("reasoning", reasoning_node.execute)
        workflow.add_node("summary", summary_node.execute)
        
        # Set entry point
        workflow.set_entry_point("triage")
        
        # Conditional routing after triage
        def route_after_triage(state: AgentState) -> Literal["retrieval", "reasoning", "summary"]:
            """
            BAD PRACTICE: Ignoring classification - always go to retrieval.
            This ensures ALL nodes run for EVERY request, regardless of actual need.
            
            Original logic was:
            - simple: go directly to summary
            - retrieval: do retrieval first
            - complex: do reasoning first
            
            Now: ALWAYS start with retrieval, then reasoning will run, then summary.
            """
            classification = state.get("classification")
            logger.info(f"Routing decision (ignored): {classification} - ALWAYS routing to retrieval")
            
            # BAD PRACTICE: Always route to retrieval to ensure all nodes execute
            return "retrieval"
        
        workflow.add_conditional_edges(
            "triage",
            route_after_triage,
            {
                "retrieval": "retrieval",
                "reasoning": "retrieval",  # BAD PRACTICE: Changed to always go to retrieval
                "summary": "retrieval"     # BAD PRACTICE: Changed to always go to retrieval
            }
        )
        
        # BAD PRACTICE: Chain all nodes together - retrieval → reasoning → summary
        # This ensures EVERY node runs for EVERY request
        workflow.add_edge("retrieval", "reasoning")
        workflow.add_edge("reasoning", "summary")
        
        # Summary is the final node
        workflow.add_edge("summary", END)
        
        # Compile graph
        app = workflow.compile()
        
        logger.info("Agent graph compiled successfully")
        return app


def create_agent_graph(
    llm_client: LLMClient,
    model_selector: ModelSelector,
    cost_tracker: CostTracker,
    node_cache: Cache,
    embedding_cache: Cache
):
    """
    Convenience function to create agent graph.
    
    Args:
        llm_client: LLM client interface
        model_selector: Model selection service
        cost_tracker: Cost tracking service
        node_cache: Node-level cache
        embedding_cache: Embedding cache
        
    Returns:
        Compiled LangGraph application
    """
    factory = AgentGraphFactory(
        llm_client=llm_client,
        model_selector=model_selector,
        cost_tracker=cost_tracker,
        node_cache=node_cache,
        embedding_cache=embedding_cache
    )
    return factory.create_graph()
