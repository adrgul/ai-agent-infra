"""
LangGraph workflow for the AI Meeting Assistant.

This module defines the state graph that orchestrates the meeting processing
pipeline from raw transcript to structured output.
"""

from typing import Dict, Any
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI

from src.models.schemas import GraphState
from src.nodes.parser import parse_transcript
from src.nodes.summarizer import summarize_meeting
from src.nodes.action_items import extract_action_items


def create_meeting_workflow(
    openai_api_key: str,
    model_name: str = "gpt-4-turbo-preview",
    temperature: float = 0.0
) -> StateGraph:
    """
    Create the LangGraph workflow for processing meeting transcripts.

    The workflow follows this pipeline:
    1. Parse/clean the raw transcript
    2. Generate summary (parallel)
    3. Extract action items (parallel)
    4. Return final state

    Args:
        openai_api_key: OpenAI API key
        model_name: Name of the OpenAI model to use
        temperature: Temperature for LLM generation (0.0 = deterministic)

    Returns:
        Compiled StateGraph ready for execution
    """
    # Initialize the LLM
    llm = ChatOpenAI(
        api_key=openai_api_key,
        model=model_name,
        temperature=temperature
    )

    # Create the state graph
    workflow = StateGraph(GraphState)

    # Define wrapper functions that inject the LLM
    def summarizer_node(state: GraphState) -> Dict[str, Any]:
        """Wrapper for summarize_meeting that injects LLM."""
        return summarize_meeting(state, llm)

    def action_items_node(state: GraphState) -> Dict[str, Any]:
        """Wrapper for extract_action_items that injects LLM."""
        return extract_action_items(state, llm)

    # Add nodes to the graph
    workflow.add_node("parse", parse_transcript)
    workflow.add_node("summarize", summarizer_node)
    workflow.add_node("extract_actions", action_items_node)

    # Define the workflow edges
    # Start -> Parse
    workflow.set_entry_point("parse")

    # Parse -> Summarize
    workflow.add_edge("parse", "summarize")

    # Summarize -> Extract Actions
    workflow.add_edge("summarize", "extract_actions")

    # Extract Actions -> End
    workflow.add_edge("extract_actions", END)

    # Compile the graph
    compiled_graph = workflow.compile()

    return compiled_graph


def create_parallel_meeting_workflow(
    openai_api_key: str,
    model_name: str = "gpt-4-turbo-preview",
    temperature: float = 0.0
) -> StateGraph:
    """
    Create an optimized workflow with parallel processing.

    This version runs summarization and action item extraction in parallel
    after parsing for better performance.

    The workflow:
    1. Parse/clean the raw transcript
    2. Branch to parallel processing:
       - Generate summary
       - Extract action items
    3. Merge results and end

    Args:
        openai_api_key: OpenAI API key
        model_name: Name of the OpenAI model to use
        temperature: Temperature for LLM generation

    Returns:
        Compiled StateGraph with parallel execution
    """
    # Initialize the LLM
    llm = ChatOpenAI(
        api_key=openai_api_key,
        model=model_name,
        temperature=temperature
    )

    # Create the state graph
    workflow = StateGraph(GraphState)

    # Define wrapper functions
    def summarizer_node(state: GraphState) -> Dict[str, Any]:
        """Wrapper for summarize_meeting that injects LLM."""
        return summarize_meeting(state, llm)

    def action_items_node(state: GraphState) -> Dict[str, Any]:
        """Wrapper for extract_action_items that injects LLM."""
        return extract_action_items(state, llm)

    def router_node(state: GraphState) -> Dict[str, Any]:
        """Router node that triggers parallel execution."""
        # This is a pass-through node for routing
        return {}

    def merge_node(state: GraphState) -> Dict[str, Any]:
        """Merge node that collects parallel results."""
        # LangGraph automatically merges state updates
        return {}

    # Add nodes
    workflow.add_node("parse", parse_transcript)
    workflow.add_node("router", router_node)
    workflow.add_node("summarize", summarizer_node)
    workflow.add_node("extract_actions", action_items_node)
    workflow.add_node("merge", merge_node)

    # Define workflow edges
    workflow.set_entry_point("parse")
    workflow.add_edge("parse", "router")

    # Parallel branches from router
    workflow.add_edge("router", "summarize")
    workflow.add_edge("router", "extract_actions")

    # Both parallel nodes feed into merge
    workflow.add_edge("summarize", "merge")
    workflow.add_edge("extract_actions", "merge")

    # Merge -> End
    workflow.add_edge("merge", END)

    # Compile the graph
    compiled_graph = workflow.compile()

    return compiled_graph


async def process_meeting_async(
    transcript: str,
    openai_api_key: str,
    model_name: str = "gpt-4-turbo-preview",
    use_parallel: bool = True
) -> GraphState:
    """
    Process a meeting transcript asynchronously.

    Args:
        transcript: Raw meeting transcript text
        openai_api_key: OpenAI API key
        model_name: Name of the OpenAI model to use
        use_parallel: Whether to use parallel processing (faster)

    Returns:
        Final GraphState with summary and action items
    """
    # Create initial state
    initial_state = GraphState(transcript=transcript)

    # Create the workflow
    if use_parallel:
        graph = create_parallel_meeting_workflow(openai_api_key, model_name)
    else:
        graph = create_meeting_workflow(openai_api_key, model_name)

    # Run the workflow
    final_state = await graph.ainvoke(initial_state)

    return GraphState(**final_state)


def process_meeting(
    transcript: str,
    openai_api_key: str,
    model_name: str = "gpt-4-turbo-preview",
    use_parallel: bool = False
) -> GraphState:
    """
    Process a meeting transcript synchronously.

    Args:
        transcript: Raw meeting transcript text
        openai_api_key: OpenAI API key
        model_name: Name of the OpenAI model to use
        use_parallel: Whether to use parallel processing

    Returns:
        Final GraphState with summary and action items
    """
    # Create initial state
    initial_state = GraphState(transcript=transcript)

    # Create the workflow
    if use_parallel:
        graph = create_parallel_meeting_workflow(openai_api_key, model_name)
    else:
        graph = create_meeting_workflow(openai_api_key, model_name)

    # Run the workflow
    final_state = graph.invoke(initial_state)

    return GraphState(**final_state)
