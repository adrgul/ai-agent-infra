"""
Service layer - LangGraph agent implementation.
Following SOLID: 
- Single Responsibility - Agent handles orchestration, delegates tool execution.
- Dependency Inversion - Agent depends on tool abstractions.
- Open/Closed - Easy to add new tools without modifying agent core logic.
"""
from typing import List, Dict, Any, Optional, Annotated, Sequence
from typing_extensions import TypedDict
import json
import logging
from datetime import datetime

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

from domain.models import Message, Memory, WorkflowState, ToolCall
from services.tools import (
    RegulationTool,
    GasExportTool
)

logger = logging.getLogger(__name__)

# Maximum iterations to prevent infinite loops in multi-step workflows
MAX_ITERATIONS = 10


class AgentState(TypedDict, total=False):
    """State object for LangGraph agent."""
    messages: Sequence[BaseMessage]
    memory: Memory
    tools_called: List[ToolCall]
    current_user_id: str
    next_action: str
    tool_decision: Dict[str, Any]
    iteration_count: int  # Track iterations to prevent infinite loops


class AIAgent:
    """
    LangGraph-based AI Agent implementing the workflow:
    Prompt → Decision → Tool → Observation → Memory → Response
    
    Graph structure: Agent → Tool → Agent → User
    """
    
    def __init__(
        self,
        openai_api_key: str,
        regulation_tool: RegulationTool = None,
        gas_export_tool: GasExportTool = None
    ):
        self.llm = ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=0.7,
            openai_api_key=openai_api_key
        )
        # Store tools
        self.tools = {}
        if regulation_tool:
            self.tools["regulation"] = regulation_tool
        if gas_export_tool:
            self.tools["gas_exported_quantity"] = gas_export_tool
        # Build LangGraph workflow
        self.workflow = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph workflow graph.
        
        Nodes:
        - agent_decide: LLM reasoning and decision-making (can loop multiple times)
        - tool_*: Individual tool execution nodes
        - agent_finalize: Final response generation
        
        Flow: agent_decide → tool → agent_decide (loop) → ... → agent_finalize
        """
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("agent_decide", self._agent_decide_node)
        workflow.add_node("agent_finalize", self._agent_finalize_node)
        
        # Add tool nodes
        for tool_name in self.tools.keys():
            workflow.add_node(f"tool_{tool_name}", self._create_tool_node(tool_name))
        
        # Set entry point
        workflow.set_entry_point("agent_decide")
        
        # Add conditional edges from agent_decide
        workflow.add_conditional_edges(
            "agent_decide",
            self._route_decision,
            {
                "final_answer": "agent_finalize",
                **{f"tool_{name}": f"tool_{name}" for name in self.tools.keys()}
            }
        )
        
        # Add edges from tools back to agent_decide (for multi-step reasoning)
        for tool_name in self.tools.keys():
            workflow.add_edge(f"tool_{tool_name}", "agent_decide")
        
        # Add edge from finalize to end
        workflow.add_edge("agent_finalize", END)
        
        # Compile the workflow
        return workflow.compile()
    
    async def _agent_decide_node(self, state: AgentState) -> AgentState:
        """
        Agent decision node: Analyzes user request and decides next action.
        """
        logger.info("Agent decision node executing")
        
        # Build context for LLM
        system_prompt = self._build_system_prompt(state["memory"])
        # Add explicit tool descriptions for the agent
        tool_descriptions = """
    Available tools:
    - regulation: Ask questions about the regulation '2008. évi LX. Gáztörvény'. Actions: 'query' (ask a question about the regulation), 'info' (get regulation information). Params: action, question, top_k (number of sources to retrieve)
    - gas_exported_quantity: Get exported gas quantity (kWh) for a given point and date range using Transparency.host. Use this tool for any request about gas flow, export, or quantity between countries (e.g. HU>UA) for any historical or recent period. Params: pointLabel (e.g. 'VIP Bereg'), from (YYYY-MM-DD), to (YYYY-MM-DD)
    """
        system_prompt += "\n" + tool_descriptions
        
        # Get last user message
        last_user_msg = None
        for msg in reversed(state["messages"]):
            if isinstance(msg, HumanMessage):
                last_user_msg = msg.content
                break
        
        # Build conversation context for decision
        recent_history = state["memory"].chat_history[-5:] if state["memory"].chat_history else []
        history_context = "\n".join([f"{msg.role}: {msg.content[:100]}" for msg in recent_history]) if recent_history else "No previous conversation"
        
        # Build list of already called tools with their arguments to prevent duplicates
        tools_called_info = [
            f"{tc.tool_name}({tc.arguments})"
            for tc in state["tools_called"]
        ]
        
        # Create decision prompt - MUST return ONLY JSON, nothing else
        decision_prompt = f"""
You must analyze the user's request and respond with ONLY a valid JSON object, nothing else.

Recent conversation context:
{history_context}

User's original request: {last_user_msg}

Tools already called with their arguments: {tools_called_info}

CRITICAL RULES:
1. NEVER call the same tool with the same arguments twice
2. If a tool was called and couldn't provide the data, do NOT retry - move to final_answer
3. If the user asks for something a tool cannot do (like future predictions), explain the limitation in final_answer
4. If the user requested multiple DIFFERENT tasks, execute them ONE AT A TIME
5. Only use "final_answer" when ALL requested tasks are complete OR a task is impossible

If the user asks about gas export, gas flow, or gas quantity between countries (e.g. HU>UA), for any historical or recent period, ALWAYS use the gas_exported_quantity tool with the appropriate parameters (pointLabel, from, to). Do NOT answer such questions from regulation or history tools.

Respond with ONLY this JSON structure (no other text, no markdown):
{{
    "action": "call_tool",
    "tool_name": "TOOL_NAME_HERE",
    "arguments": {{...}},
    "reasoning": "brief explanation"
}}

Examples:
- Gas export: {{"action": "call_tool", "tool_name": "gas_exported_quantity", "arguments": {{"pointLabel": "VIP Bereg", "from": "2025-01-01", "to": "2025-12-31"}}, "reasoning": "get gas export data"}}
- Final answer: {{"action": "final_answer", "reasoning": "all tasks completed"}}

IMPORTANT: The "action" field must ALWAYS be either "call_tool" or "final_answer" - NEVER use a tool name as the action!
"""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=decision_prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        
        # Parse decision
        try:
            # Try to extract JSON from the response
            content = response.content.strip()
            
            # If response contains markdown code blocks, extract JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            decision = json.loads(content)
            logger.info(f"Agent decision: {decision}")
            
            state["next_action"] = decision.get("action", "final_answer")
            
            # Store decision for tool execution
            if decision.get("action") == "call_tool":
                state["tool_decision"] = decision
                # Increment iteration count when calling a tool
                state["iteration_count"] = state.get("iteration_count", 0) + 1
            
        except (json.JSONDecodeError, IndexError, AttributeError) as e:
            logger.error(f"Failed to parse agent decision: {e}, defaulting to final_answer")
            logger.error(f"Response content: {response.content[:200]}")
            state["next_action"] = "final_answer"
        
        return state
    
    def _route_decision(self, state: AgentState) -> str:
        """Route to next node based on agent decision."""
        # Check iteration limit to prevent infinite loops
        if state.get("iteration_count", 0) >= MAX_ITERATIONS:
            logger.warning(f"Max iterations ({MAX_ITERATIONS}) reached, forcing finalize")
            return "final_answer"
        
        action = state.get("next_action", "final_answer")
        
        if action == "call_tool" and "tool_decision" in state:
            tool_name = state["tool_decision"].get("tool_name")
            if tool_name in self.tools:
                return f"tool_{tool_name}"
        
        return "final_answer"
    
    def _create_tool_node(self, tool_name: str):
        """Create a tool execution node."""
        async def tool_node(state: AgentState) -> AgentState:
            logger.info(f"Executing tool: {tool_name}")
            
            tool = self.tools[tool_name]
            decision = state.get("tool_decision", {})
            arguments = decision.get("arguments", {})
            
            # Add user_id for file creation tool
            if tool_name == "create_file":
                arguments["user_id"] = state["current_user_id"]
            
            # Execute tool
            try:
                result = await tool.execute(**arguments)
                
                # Record tool call
                tool_call = ToolCall(
                    tool_name=tool_name,
                    arguments=arguments,
                    result=result.get("data") if result.get("success") else None,
                    error=result.get("error") if not result.get("success") else None
                )
                state["tools_called"].append(tool_call)
                
                # Add system message - include full message content if available
                # This ensures the LLM sees the actual tool output (e.g., station names)
                if result.get("message"):
                    system_msg = result.get("message")
                else:
                    system_msg = result.get("system_message", f"Tool {tool_name} executed")
                state["messages"].append(SystemMessage(content=system_msg))
                
                logger.info(f"Tool {tool_name} completed: {result.get('success', False)}")
                
            except Exception as e:
                logger.error(f"Tool {tool_name} error: {e}")
                error_msg = f"Error executing {tool_name}: {str(e)}"
                state["messages"].append(SystemMessage(content=error_msg))
                state["tools_called"].append(ToolCall(
                    tool_name=tool_name,
                    arguments=arguments,
                    error=str(e)
                ))
            
            return state
        
        return tool_node
    
    async def _agent_finalize_node(self, state: AgentState) -> AgentState:
        """
        Agent finalize node: Generates final response to user.
        """
        logger.info("Agent finalize node executing")
        
        # Build final prompt with memory and tool results
        system_prompt = self._build_system_prompt(state["memory"])
        
        # Get the user's original message to detect language
        user_message = ""
        for msg in state["messages"]:
            if isinstance(msg, HumanMessage):
                user_message = msg.content
                break
        
        # Detect language of the user's question
        user_message_lower = user_message.lower()
        # Use word boundaries to avoid false matches
        import re
        
        # Check for Hungarian-specific words first (more specific)
        hungarian_words = r'\b(ki|kicsoda|mi|milyen|hol|mikor|miért|hogy|hogyan|van|vannak|volt|lesz|lennék|jogszabály|rendelet|törvény|szabályozás|szabályozási)\b'
        english_words = r'\b(who|what|where|when|why|how|is|are|was|were|the|regulation|law|act|can|could|would|should)\b'
        
        hungarian_matches = len(re.findall(hungarian_words, user_message_lower))
        english_matches = len(re.findall(english_words, user_message_lower))
        
        logger.info(f"Language detection: '{user_message[:50]}' - HU matches: {hungarian_matches}, EN matches: {english_matches}")
        
        if hungarian_matches > english_matches:
            detected_language = "Hungarian"
            language_instruction = "Válaszolj magyarul. A válasznak magyar nyelvűnek kell lennie."
        else:
            detected_language = "English"
            language_instruction = "You MUST respond in English. Translate any Hungarian content to English."
        
        logger.info(f"Detected user question language: {detected_language}")
        
        # Get conversation context
        conversation_history = "\n".join([
            f"{msg.__class__.__name__}: {msg.content}"
            for msg in state["messages"][-10:]  # Last 10 messages
        ])
        
        final_prompt = f"""
Generate a natural language response to the user based on the conversation history and any tool results.

Conversation:
{conversation_history}

CRITICAL LANGUAGE INSTRUCTION:
{language_instruction}

Important:
- Be helpful and conversational
- Use information from tool results if available
- Keep the response concise but complete
- The user asked in {detected_language}, so your entire response must be in {detected_language}
"""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=final_prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        
        # Add assistant message
        state["messages"].append(AIMessage(content=response.content))
        
        logger.info("Agent finalized response")
        
        return state
    
    def _build_system_prompt(self, memory: Memory) -> str:
        """Build system prompt with memory context."""
        preferences = memory.preferences
        workflow = memory.workflow_state
        
        # Build user info section
        user_info = []
        if preferences.get('name'):
            user_info.append(f"- Name: {preferences['name']}")
        user_info.append(f"- Language: {preferences.get('language', 'hu')}")
        user_info.append(f"- Default city: {preferences.get('default_city', 'Budapest')}")
        
        # Add any other preferences
        for key, value in preferences.items():
            if key not in ['name', 'language', 'default_city']:
                user_info.append(f"- {key.replace('_', ' ').title()}: {value}")
        
        prompt = f"""You are a helpful AI assistant with access to various tools.

User preferences:
{chr(10).join(user_info)}

"""
        
        # Add recent conversation history for context
        if memory.chat_history:
            recent_history = memory.chat_history[-10:]  # Last 10 messages
            history_text = "\n".join([
                f"{msg.role}: {msg.content[:150]}"  # Truncate long messages
                for msg in recent_history
            ])
            prompt += f"\nRecent conversation history:\n{history_text}\n\n"
        
        if workflow.flow:
            prompt += f"\nCurrent workflow: {workflow.flow} (step {workflow.step}/{workflow.total_steps})\n"
        
        # Add personalization instruction
        if preferences.get('name'):
            prompt += f"\nAddress the user by their name ({preferences['name']}) when appropriate.\n"
        
        return prompt
    
    async def run(
        self,
        user_message: str,
        memory: Memory,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Run the agent workflow.
        
        Args:
            user_message: User's input message
            memory: Memory context (preferences, history, workflow state)
            user_id: Current user ID
        
        Returns:
            Dict containing final_answer, tools_called, and updated memory
        """
        logger.info(f"Agent run started for user {user_id}")
        
        # Initialize state
        initial_state: AgentState = {
            "messages": [HumanMessage(content=user_message)],
            "memory": memory,
            "tools_called": [],
            "current_user_id": user_id,
            "next_action": "",
            "iteration_count": 0
        }
        
        # Run workflow with increased recursion limit for multi-step workflows
        final_state = await self.workflow.ainvoke(
            initial_state,
            {"recursion_limit": 50}
        )
        
        # Extract final answer
        final_answer = ""
        for msg in reversed(final_state["messages"]):
            if isinstance(msg, AIMessage):
                final_answer = msg.content
                break
        
        logger.info("Agent run completed")
        
        return {
            "final_answer": final_answer,
            "tools_called": final_state["tools_called"],
            "messages": final_state["messages"],
            "memory": final_state["memory"]
        }
