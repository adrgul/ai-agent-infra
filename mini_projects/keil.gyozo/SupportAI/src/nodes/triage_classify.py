"""Triage classification node - assigns category, priority, and SLA."""

import logging
from datetime import datetime, timezone

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field, field_validator

from ..models.state import SupportTicketState
from ..services import get_llm

logger = logging.getLogger(__name__)


class TriageResult(BaseModel):
    """Structured output for triage classification."""

    category: str = Field(..., description="Main category")
    subcategory: str = Field(..., description="Specific subcategory")
    priority: str = Field(..., description="Priority: P1 | P2 | P3")
    sla_hours: int = Field(..., ge=1, le=168, description="SLA in hours")
    suggested_team: str = Field(..., description="Team to assign to")
    confidence: float = Field(..., ge=0, le=1, description="Classification confidence")

    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v: str) -> str:
        """Validate priority is P1, P2, or P3."""
        if v not in ['P1', 'P2', 'P3']:
            raise ValueError(f"Invalid priority: {v}. Must be P1, P2, or P3")
        return v


async def triage_classify_node(state: SupportTicketState) -> dict:
    """Classify ticket and assign priority and SLA.

    This node performs the core triage function, determining:
    - Category and subcategory
    - Priority level (P1/P2/P3)
    - SLA hours
    - Suggested team for assignment

    Priority rules:
    - P1 (Critical): 4 hours - Service outages, security issues, payment blocking issues
    - P2 (High): 24 hours - Significant problems, frustrated customers, billing errors
    - P3 (Normal): 72 hours - General inquiries, feature requests, minor issues

    Args:
        state: Current workflow state with problem_type and sentiment

    Returns:
        Dictionary with triage classification fields
    """
    logger.info(f"Triaging ticket: {state.get('ticket_id')}")

    llm = get_llm(temperature=0)
    structured_llm = llm.with_structured_output(TriageResult)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a support ticket triage specialist.

**Categories:**
- Billing: Payments, charges, invoices, refunds, subscriptions
- Technical: Bugs, errors, performance issues, features not working
- Account: Login, password, profile, access, permissions
- Feature Request: New features, enhancements, product suggestions

**Priority Levels:**
- P1 (Critical, 4h SLA): Service outages, security breaches, payment completely blocked
- P2 (High, 24h SLA): Significant issues, billing errors, frustrated customers, partial service impact
- P3 (Normal, 72h SLA): General questions, minor issues, feature requests, satisfied/neutral tone

**Teams:**
- Finance Team: Billing, payments, refunds, invoices
- Engineering: Technical issues, bugs, performance
- Account Management: Account access, profile, permissions
- Product: Feature requests, enhancements

**IMPORTANT:**
- Frustrated customers should generally get priority boost (P2 minimum)
- Billing issues affecting payments are typically P2 (or P1 if completely blocked)
- Multiple issues or urgent language may warrant higher priority
- Provide a confidence score based on clarity of the message"""),
        ("human", """Ticket ID: {ticket_id}
Customer: {customer_name}
Problem Type: {problem_type}
Sentiment: {sentiment}
Message: {message}

Classify this ticket with category, priority, SLA, and suggested team.""")
    ])

    chain = prompt | structured_llm

    try:
        result = await chain.ainvoke({
            "ticket_id": state.get("ticket_id", "UNKNOWN"),
            "customer_name": state.get("customer_name", "Customer"),
            "problem_type": state["problem_type"],
            "sentiment": state["sentiment"],
            "message": state["raw_message"]
        })

        logger.info(
            f"Triage complete - Category: {result.category}/{result.subcategory}, "
            f"Priority: {result.priority}, SLA: {result.sla_hours}h, "
            f"Team: {result.suggested_team}, Confidence: {result.confidence:.2f}"
        )

        return {
            "category": result.category,
            "subcategory": result.subcategory,
            "priority": result.priority,
            "sla_hours": result.sla_hours,
            "suggested_team": result.suggested_team,
            "triage_confidence": result.confidence,
        }

    except Exception as e:
        logger.error(f"Triage classification failed: {e}")
        # Provide safe defaults
        return {
            "category": "Technical",
            "subcategory": "General Issue",
            "priority": "P3",
            "sla_hours": 72,
            "suggested_team": "Engineering",
            "triage_confidence": 0.0,
            "errors": [f"Triage error: {str(e)}"]
        }
