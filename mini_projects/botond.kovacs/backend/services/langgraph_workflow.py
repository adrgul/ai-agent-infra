from langgraph import Graph, Node
from langgraph.nodes import AgentNode, ToolNode
from tools.gas_exported_quantity import fetch_gas_exported_quantity
from tools.json_history_search import JSONHistorySearchTool

# Define the LangGraph workflow
def create_langgraph_workflow():
    graph = Graph()

    # Define nodes
    agent_decide = AgentNode(
        name="agent_decide",
        description="Agent decides whether to call a tool or provide a final answer."
    )

    gas_tool = ToolNode(
        name="gas_exported_quantity_tool",
        description="Fetches gas exported quantity data.",
        tool_function=fetch_gas_exported_quantity  # Connected the actual function
    )

    history_tool = ToolNode(
        name="history_search_tool",
        description="Searches conversation history.",
        tool_function=None  # To be implemented
    )

    agent_finalize = AgentNode(
        name="agent_finalize",
        description="Agent finalizes the response after tool usage."
    )

    # Add nodes to graph
    graph.add_node(agent_decide)
    graph.add_node(gas_tool)
    graph.add_node(history_tool)
    graph.add_node(agent_finalize)

    # Define edges
    graph.add_edge(agent_decide, gas_tool, condition="tool_name == 'gas_exported_quantity_tool'")
    graph.add_edge(agent_decide, history_tool, condition="tool_name == 'history_search_tool'")
    graph.add_edge(gas_tool, agent_finalize)
    graph.add_edge(history_tool, agent_finalize)

    # Initialize the JSON history search tool
    history_search_tool_instance = JSONHistorySearchTool()
    history_tool.tool_function = history_search_tool_instance.search

    return graph