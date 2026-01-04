"""
Pydantic models for structured LLM responses.
"""

from typing import Literal

from pydantic import BaseModel, Field


class TicketAnalysis(BaseModel):
    """Ticket analysis result - structured LLM output."""

    language: str = Field(
        description="The language of the ticket (e.g., Hungarian, English, German)"
    )
    sentiment: Literal["frustrated", "neutral", "satisfied"] = Field(
        description="The customer's sentiment"
    )
    category: Literal["Billing", "Technical", "Account", "Feature Request", "General"] = Field(
        description="The ticket category"
    )
    priority: Literal["P1", "P2", "P3", "P4"] = Field(
        description="Priority: P1=Critical, P2=High, P3=Medium, P4=Low"
    )
    routing: str = Field(
        description="Suggested team (e.g., Finance Team, IT Support)"
    )
