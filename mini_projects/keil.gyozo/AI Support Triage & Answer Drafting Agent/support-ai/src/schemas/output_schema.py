"""
Pydantic schemas for SupportAI output validation.

Defines the complete JSON output structure for the support agent workflow.
"""

from datetime import datetime
from typing import List, Literal
from pydantic import BaseModel, Field, HttpUrl


class TriageOutput(BaseModel):
    """Triage classification results."""

    category: str = Field(..., description="Main category (e.g., 'Billing - Invoice Issue')")
    subcategory: str = Field(..., description="Specific subcategory (e.g., 'Duplicate Charge')")
    priority: Literal["P1", "P2", "P3"] = Field(..., description="Priority level")
    sla_hours: int = Field(..., description="SLA time in hours")
    suggested_team: str = Field(..., description="Recommended team for handling")
    sentiment: Literal["frustrated", "neutral", "satisfied"] = Field(..., description="Customer sentiment")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Classification confidence score")

    model_config = {
        "json_schema_extra": {
            "example": {
                "category": "Billing - Invoice Issue",
                "subcategory": "Duplicate Charge",
                "priority": "P2",
                "sla_hours": 24,
                "suggested_team": "Finance Team",
                "sentiment": "frustrated",
                "confidence": 0.92
            }
        }
    }


class AnswerDraft(BaseModel):
    """Generated response draft."""

    greeting: str = Field(..., description="Personalized greeting")
    body: str = Field(..., description="Main response content with citations")
    closing: str = Field(..., description="Professional closing")
    tone: str = Field(..., description="Response tone (e.g., 'empathetic_professional')")

    model_config = {
        "json_schema_extra": {
            "example": {
                "greeting": "Dear John,",
                "body": "Thank you for reaching out regarding the duplicate charge...",
                "closing": "Best regards,\nSupport Team",
                "tone": "empathetic_professional"
            }
        }
    }


class Citation(BaseModel):
    """Knowledge base citation reference."""

    doc_id: str = Field(..., description="Document identifier")
    chunk_id: str = Field(..., description="Chunk identifier within document")
    title: str = Field(..., description="Document title")
    score: float = Field(..., ge=0.0, le=1.0, description="Relevance score")
    url: HttpUrl = Field(..., description="Document URL")

    model_config = {
        "json_schema_extra": {
            "example": {
                "doc_id": "KB-1234",
                "chunk_id": "c-45",
                "title": "How to Handle Duplicate Charges",
                "score": 0.89,
                "url": "https://kb.company.com/billing/duplicate-charges"
            }
        }
    }


class PolicyCheck(BaseModel):
    """Policy compliance validation results."""

    refund_promise: bool = Field(..., description="Whether draft promises refunds")
    sla_mentioned: bool = Field(..., description="Whether SLA is mentioned")
    escalation_needed: bool = Field(..., description="Whether human escalation required")
    compliance: Literal["passed", "failed"] = Field(..., description="Overall compliance status")

    model_config = {
        "json_schema_extra": {
            "example": {
                "refund_promise": False,
                "sla_mentioned": True,
                "escalation_needed": False,
                "compliance": "passed"
            }
        }
    }


class SupportAgentOutput(BaseModel):
    """Complete output from the SupportAI agent."""

    ticket_id: str = Field(..., description="Unique ticket identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Processing timestamp")
    triage: TriageOutput = Field(..., description="Triage classification results")
    answer_draft: AnswerDraft = Field(..., description="Generated response draft")
    citations: List[Citation] = Field(..., description="Knowledge base citations")
    policy_check: PolicyCheck = Field(..., description="Policy compliance check")

    model_config = {
        "json_schema_extra": {
            "example": {
                "ticket_id": "TKT-2025-12-09-4567",
                "timestamp": "2025-12-09T14:32:00Z",
                "triage": {
                    "category": "Billing - Invoice Issue",
                    "subcategory": "Duplicate Charge",
                    "priority": "P2",
                    "sla_hours": 24,
                    "suggested_team": "Finance Team",
                    "sentiment": "frustrated",
                    "confidence": 0.92
                },
                "answer_draft": {
                    "greeting": "Dear John,",
                    "body": "Thank you for reaching out regarding the duplicate charge...",
                    "closing": "Best regards,\nSupport Team",
                    "tone": "empathetic_professional"
                },
                "citations": [
                    {
                        "doc_id": "KB-1234",
                        "chunk_id": "c-45",
                        "title": "How to Handle Duplicate Charges",
                        "score": 0.89,
                        "url": "https://kb.company.com/billing/duplicate-charges"
                    }
                ],
                "policy_check": {
                    "refund_promise": False,
                    "sla_mentioned": True,
                    "escalation_needed": False,
                    "compliance": "passed"
                }
            }
        }
    }