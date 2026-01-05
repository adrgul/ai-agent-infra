"""Ticket input/output models."""

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


def utc_now() -> str:
    """Return current UTC time as ISO format string.

    ⚠️ IMPORTANT: datetime.utcnow() is DEPRECATED in Python 3.12+!
    Always use datetime.now(timezone.utc) instead.
    """
    return datetime.now(timezone.utc).isoformat()


class TicketInput(BaseModel):
    """Input model for incoming support tickets.

    NOTE: Using EmailStr requires pydantic[email] extra!
    """

    ticket_id: str = Field(..., description="Unique ticket identifier")
    raw_message: str = Field(..., min_length=10, description="Customer's message")
    customer_name: str = Field(..., min_length=1, description="Customer name")
    customer_email: EmailStr = Field(..., description="Customer email address")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "ticket_id": "TKT-2025-001",
                    "raw_message": "I was charged twice for my subscription this month. Please help!",
                    "customer_name": "John Doe",
                    "customer_email": "john.doe@example.com"
                }
            ]
        }
    }


class AnswerDraft(BaseModel):
    """Draft response structure."""

    greeting: str = Field(..., description="Personalized greeting")
    body: str = Field(..., description="Main response body with [DOC-ID] citations")
    closing: str = Field(..., description="Professional closing")
    tone: str = Field(
        default="empathetic_professional",
        description="Response tone: empathetic_professional | formal | casual"
    )


class TriageOutput(BaseModel):
    """Triage classification output."""

    category: str = Field(..., description="Main category")
    subcategory: str = Field(..., description="Specific subcategory")
    priority: str = Field(..., pattern="^P[1-3]$", description="Priority level: P1/P2/P3")
    sla_hours: int = Field(..., ge=1, le=168, description="SLA in hours")
    suggested_team: str = Field(..., description="Recommended team for assignment")
    sentiment: str = Field(..., description="Customer sentiment")
    confidence: float = Field(..., ge=0, le=1, description="Classification confidence")


class CitationOutput(BaseModel):
    """Citation reference for knowledge base articles."""

    doc_id: str = Field(..., description="Document ID")
    chunk_id: str = Field(..., description="Specific chunk ID")
    title: str = Field(..., description="Document title")
    score: float = Field(..., ge=0, le=1, description="Relevance score")
    url: str = Field(..., description="Knowledge base URL")


class PolicyCheckOutput(BaseModel):
    """Policy compliance validation result."""

    refund_promise: bool = Field(..., description="Contains refund promise")
    sla_mentioned: bool = Field(..., description="Mentions SLA/timeline")
    escalation_needed: bool = Field(..., description="Requires escalation")
    compliance: str = Field(
        ...,
        pattern="^(passed|failed|warning)$",
        description="Overall compliance status"
    )
    issues: Optional[list[str]] = Field(default=None, description="Compliance issues found")


class TicketOutput(BaseModel):
    """Complete output model for processed ticket."""

    ticket_id: str = Field(..., description="Ticket identifier")
    timestamp: str = Field(default_factory=utc_now, description="Processing timestamp")

    triage: TriageOutput = Field(..., description="Triage classification results")
    answer_draft: AnswerDraft = Field(..., description="Generated response draft")
    citations: list[CitationOutput] = Field(..., description="Knowledge base citations")
    policy_check: PolicyCheckOutput = Field(..., description="Policy compliance check")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "ticket_id": "TKT-2025-001",
                    "timestamp": "2025-01-15T10:30:00+00:00",
                    "triage": {
                        "category": "Billing",
                        "subcategory": "Duplicate Charge",
                        "priority": "P2",
                        "sla_hours": 24,
                        "suggested_team": "Finance Team",
                        "sentiment": "frustrated",
                        "confidence": 0.92
                    },
                    "answer_draft": {
                        "greeting": "Hi John,",
                        "body": "I understand your concern about the duplicate charge...",
                        "closing": "Best regards,\nSupport Team",
                        "tone": "empathetic_professional"
                    },
                    "citations": [
                        {
                            "doc_id": "KB-1234",
                            "chunk_id": "KB-1234-c-45",
                            "title": "Duplicate Charge Resolution",
                            "score": 0.89,
                            "url": "https://kb.company.com/billing/duplicate"
                        }
                    ],
                    "policy_check": {
                        "refund_promise": False,
                        "sla_mentioned": True,
                        "escalation_needed": False,
                        "compliance": "passed"
                    }
                }
            ]
        }
    }
