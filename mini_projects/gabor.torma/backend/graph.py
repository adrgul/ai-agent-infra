from langgraph.graph import StateGraph, START, END
from state import MeetingState
from nodes import note_taker, task_assigner, summarizer, metadata_extractor

def build_graph():
    """
    Constructs and compiles the MeetingAI StateGraph.
    """
    # Initialize StateGraph with MeetingState
    workflow = StateGraph(MeetingState)
    
    # Add nodes
    workflow.add_node("note_taker", note_taker)
    workflow.add_node("task_assigner", task_assigner)
    workflow.add_node("metadata_extractor", metadata_extractor)
    workflow.add_node("summarizer", summarizer)
    
    # Define topology
    # Parallel execution from START
    workflow.add_edge(START, "note_taker")
    workflow.add_edge(START, "task_assigner")
    workflow.add_edge(START, "metadata_extractor")
    
    # Synchronization: both must finish before summarizer
    workflow.add_edge("note_taker", "summarizer")
    workflow.add_edge("task_assigner", "summarizer")
    workflow.add_edge("metadata_extractor", "summarizer")
    
    # Finish after summarizer
    workflow.add_edge("summarizer", END)
    
    # Compile the graph
    app = workflow.compile()
    
    return app
