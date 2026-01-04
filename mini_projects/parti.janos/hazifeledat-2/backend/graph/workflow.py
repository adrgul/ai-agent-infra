from langgraph.graph import StateGraph, END
from typing import Literal

from graph.state import AgentState
from services.router import RouterService
from services.retriever import RetrieverService
from services.generator import ResponseGenerator
from services.tools import TOOL_REGISTRY

# Initialize services
router_service = RouterService()
retriever_service = RetrieverService()
response_generator = ResponseGenerator()

async def router_node(state: AgentState) -> AgentState:
    """Decides the domain and intent of the query."""
    user_input = state["input"]
    routing_result = await router_service.route_query(user_input)
    
    print(f"DEBUG: Routed to Domain='{routing_result.get('domain')}', Intent='{routing_result.get('intent')}', Tool='{routing_result.get('tool')}'")
    
    return {
        "domain": routing_result.get("domain"),
        "intent": routing_result.get("intent"),
        "tool_name": routing_result.get("tool"),
        "tool_args": routing_result.get("tool_args", {})
    }

async def retriever_node(state: AgentState) -> AgentState:
    """Retrieves relevant documents based on domain."""
    query = state["input"]
    domain = state["domain"]
    
    print(f"DEBUG: Retrieving for '{query}' in '{domain}'...")
    
    # Retrieve documents with scores for better citation quality
    try:
        docs_with_scores = await retriever_service.retrieve_with_scores(query, domain)
        docs = [doc for doc, score in docs_with_scores]
        scores = [score for doc, score in docs_with_scores]
        print(f"DEBUG: Found {len(docs)} documents with scores.")
    except Exception as e:
        print(f"DEBUG: Error retrieving with scores: {e}. Falling back to regular retrieval.")
        # Fallback to regular retrieval if scores are not available
        docs = await retriever_service.retrieve(query, domain)
        scores = None
        print(f"DEBUG: Found {len(docs)} documents.")
    
    # Extract citations from retrieved documents with scores
    citations = response_generator.extract_citations(docs, scores)
    
    return {
        "retrieved_docs": docs,
        "citations": citations
    }

async def action_node(state: AgentState) -> AgentState:
    """Executes a tool if intent is action."""
    tool_name = state["tool_name"]
    tool_args = state["tool_args"]
    citations = state.get("citations", [])  # Preserve citations if any
    
    response_msg = ""
    
    if tool_name in TOOL_REGISTRY:
        tool_func = TOOL_REGISTRY[tool_name]
        try:
            # In a real app, user_id would come from state/context
            if "user_id" not in tool_args and tool_name == "check_vacation_balance":
                tool_args["user_id"] = "current_user"
                
            result = tool_func(**tool_args)
            response_msg = f"Action executed successfully: {result['message']}"
            if "link" in result:
                response_msg += f" [Link]({result['link']})"
        except Exception as e:
            response_msg = f"Error executing action: {str(e)}"
    else:
        response_msg = f"Unknown tool: {tool_name}"
        
    return {
        "final_response": response_msg,
        "citations": citations  # Preserve citations
    }

async def generation_node(state: AgentState) -> AgentState:
    """Generates final response using RAG."""
    query = state["input"]
    docs = state["retrieved_docs"]
    domain = state["domain"]
    citations = state.get("citations", [])
    
    response = await response_generator.generate_response(query, docs, domain)
    return {
        "final_response": response,
        "citations": citations  # Preserve citations
    }

def decide_next_step(state: AgentState) -> Literal["retriever", "action"]:
    """Conditional logic to determine next node."""
    if state["intent"] == "action" and state["tool_name"] != "none":
        return "action"
    return "retriever"

def build_graph():
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("router", router_node)
    workflow.add_node("retriever", retriever_node)
    workflow.add_node("generator", generation_node)
    workflow.add_node("action", action_node)
    
    # Set entry point
    workflow.set_entry_point("router")
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "router",
        decide_next_step,
        {
            "retriever": "retriever",
            "action": "action"
        }
    )
    
    # Standard edges
    workflow.add_edge("retriever", "generator")
    workflow.add_edge("generator", END)
    workflow.add_edge("action", END)
    
    return workflow.compile()
