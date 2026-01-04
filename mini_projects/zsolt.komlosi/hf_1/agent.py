"""
LangGraph Agent for Support Ticket SLA Analysis.
"""

from datetime import datetime
from typing import Annotated, Optional, TypedDict

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

from config import get_settings
from models import TicketAnalysis
from tools import get_location_info, get_holidays, calculate_sla_deadline


class AgentState(TypedDict):
    """State for the LangGraph agent."""

    messages: Annotated[list[BaseMessage], add_messages]
    ticket_text: str
    ip_address: Optional[str]

    # Analysis results
    language: Optional[str]
    sentiment: Optional[str]
    category: Optional[str]
    priority: Optional[str]
    routing: Optional[str]

    # Location data
    location_info: Optional[dict]
    holidays: Optional[list]

    # SLA data
    sla_info: Optional[dict]

    # Final response
    final_response: Optional[str]


# System prompt in English (better LLM performance)
ANALYSIS_PROMPT = """You are an SLA Advisor Agent for customer support ticket analysis.

Analyze the ticket and determine:
1. Language - What language is the ticket written in?
2. Sentiment - Is the customer frustrated, neutral, or satisfied?
3. Category - Billing, Technical, Account, Feature Request, or General?
4. Priority based on urgency:
   - P1 (Critical): System down, security breach, payment failure, words like URGENT
   - P2 (High): Functionality broken, login issues, urgent requests
   - P3 (Medium): General questions, minor issues
   - P4 (Low): Feature requests, feedback, general inquiries
5. Routing - Which team should handle this? (Finance Team, IT Support, Account Team, Product Team, General Support)

Analyze this ticket:
{ticket_text}"""

FINAL_RESPONSE_PROMPT = """Based on the analysis data, create a HUNGARIAN language response.

Ticket: {ticket_text}
Analysis: {analysis}
Location: {location}
SLA: {sla}

Format the response in Hungarian with these sections:
- TICKET ELEMZÉS (nyelv, hangulat, kategória)
- ÜGYFÉL KONTEXTUS (helyszín, időzóna - if available)
- SLA JAVASLAT (prioritás, válaszidő, határidő)
- ROUTING JAVASLAT (melyik csapat)

Be concise but informative. Use clear formatting."""


class SLAAdvisorAgent:
    """SLA Advisor Agent with LangGraph."""

    def __init__(self):
        settings = get_settings()

        # Base LLM
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0.3,
        )

        # Structured output LLM for ticket analysis
        self.analysis_llm = self.llm.with_structured_output(TicketAnalysis)

        # Build graph
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("analyze_ticket", self._analyze_ticket_node)
        workflow.add_node("get_location", self._get_location_node)
        workflow.add_node("get_holidays", self._get_holidays_node)
        workflow.add_node("calculate_sla", self._calculate_sla_node)
        workflow.add_node("generate_response", self._generate_response_node)

        # Define edges
        workflow.set_entry_point("analyze_ticket")
        workflow.add_conditional_edges(
            "analyze_ticket",
            self._should_get_location,
            {
                "get_location": "get_location",
                "calculate_sla": "calculate_sla",
            }
        )
        workflow.add_edge("get_location", "get_holidays")
        workflow.add_edge("get_holidays", "calculate_sla")
        workflow.add_edge("calculate_sla", "generate_response")
        workflow.add_edge("generate_response", END)

        return workflow.compile()

    def _should_get_location(self, state: AgentState) -> str:
        """Decide whether location lookup is needed."""
        if state.get("ip_address"):
            return "get_location"
        return "calculate_sla"

    def _analyze_ticket_node(self, state: AgentState) -> dict:
        """Node: Analyze ticket with LLM using structured output."""
        print("  [1/5] Ticket elemzése...")

        # Structured output - directly get TicketAnalysis object
        analysis: TicketAnalysis = self.analysis_llm.invoke(
            ANALYSIS_PROMPT.format(ticket_text=state["ticket_text"])
        )

        return {
            "language": analysis.language,
            "sentiment": analysis.sentiment,
            "category": analysis.category,
            "priority": analysis.priority,
            "routing": analysis.routing,
            "messages": [SystemMessage(content=f"Ticket analyzed: {analysis.model_dump()}")]
        }

    def _get_location_node(self, state: AgentState) -> dict:
        """Node: Query location based on IP address."""
        print("  [2/5] Lokáció lekérdezése...")

        ip_address = state.get("ip_address")
        if not ip_address:
            return {"location_info": None}

        location_info = get_location_info.invoke({"ip_address": ip_address})

        return {
            "location_info": location_info,
            "messages": [SystemMessage(content=f"Location retrieved: {location_info}")]
        }

    def _get_holidays_node(self, state: AgentState) -> dict:
        """Node: Query public holidays."""
        print("  [3/5] Munkaszüneti napok ellenőrzése...")

        location_info = state.get("location_info")
        if not location_info or location_info.get("error"):
            return {"holidays": []}

        country_code = location_info.get("country_code", "")
        if not country_code:
            return {"holidays": []}

        holidays_result = get_holidays.invoke({
            "country_code": country_code,
            "year": datetime.now().year
        })

        holidays = holidays_result.get("holidays", []) if not holidays_result.get("error") else []

        return {
            "holidays": holidays,
            "messages": [SystemMessage(content=f"Holidays retrieved: {len(holidays)} found")]
        }

    def _calculate_sla_node(self, state: AgentState) -> dict:
        """Node: Calculate SLA deadline."""
        print("  [4/5] SLA számítása...")

        priority = state.get("priority", "P3")
        location_info = state.get("location_info") or {}
        timezone = location_info.get("timezone", "UTC")
        country_code = location_info.get("country_code", "")

        sla_info = calculate_sla_deadline.invoke({
            "timezone": timezone,
            "priority": priority,
            "country_code": country_code
        })

        return {
            "sla_info": sla_info,
            "messages": [SystemMessage(content=f"SLA calculated: {sla_info}")]
        }

    def _generate_response_node(self, state: AgentState) -> dict:
        """Node: Generate final response in Hungarian."""
        print("  [5/5] Válasz generálása...")

        analysis = {
            "language": state.get("language"),
            "sentiment": state.get("sentiment"),
            "category": state.get("category"),
            "priority": state.get("priority"),
            "routing": state.get("routing"),
        }

        location = state.get("location_info") or {"message": "No IP address provided"}
        sla = state.get("sla_info") or {}

        response = self.llm.invoke([
            SystemMessage(content="You are a helpful assistant. Always respond in Hungarian."),
            HumanMessage(content=FINAL_RESPONSE_PROMPT.format(
                ticket_text=state["ticket_text"],
                analysis=analysis,
                location=location,
                sla=sla
            )),
        ])

        return {
            "final_response": response.content,
            "messages": [SystemMessage(content="Response generated")]
        }

    def analyze(self, ticket_text: str, ip_address: str = None) -> str:
        """
        Analyze support ticket and provide SLA recommendation.

        Args:
            ticket_text: The ticket text
            ip_address: Optional IP address for customer location

        Returns:
            Analysis result in Hungarian
        """
        initial_state: AgentState = {
            "messages": [HumanMessage(content=ticket_text)],
            "ticket_text": ticket_text,
            "ip_address": ip_address,
            "language": None,
            "sentiment": None,
            "category": None,
            "priority": None,
            "routing": None,
            "location_info": None,
            "holidays": None,
            "sla_info": None,
            "final_response": None,
        }

        # Run graph
        final_state = self.graph.invoke(initial_state)

        return final_state.get("final_response", "An error occurred during analysis.")

    def reset_history(self):
        """Clear chat history."""
        pass
