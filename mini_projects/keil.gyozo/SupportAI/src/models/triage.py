"""Triage result models."""

from pydantic import BaseModel, Field


class TriageResult(BaseModel):
    """Structured output for triage classification.

    Used with LangChain's with_structured_output() for guaranteed schema.
    """

    category: str = Field(..., description="Main category: Billing, Technical, Account, Feature Request")
    subcategory: str = Field(..., description="Specific subcategory")
    priority: str = Field(..., pattern="^P[1-3]$", description="Priority: P1 (4h) | P2 (24h) | P3 (72h)")
    sla_hours: int = Field(..., ge=1, le=168, description="SLA in hours")
    suggested_team: str = Field(..., description="Team: Finance, Engineering, Account Management, Product")
    confidence: float = Field(..., ge=0, le=1, description="Classification confidence score")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "category": "Billing",
                    "subcategory": "Duplicate Charge",
                    "priority": "P2",
                    "sla_hours": 24,
                    "suggested_team": "Finance Team",
                    "confidence": 0.92
                }
            ]
        }
    }


class TriageClassification(BaseModel):
    """Extended triage classification with metadata."""

    category: str
    subcategory: str
    priority: str
    sla_hours: int
    suggested_team: str
    sentiment: str  # frustrated | neutral | satisfied
    confidence: float
    reasoning: str = Field(default="", description="Explanation for classification")

    def to_dict(self) -> dict:
        """Convert to dictionary for state updates."""
        return {
            "category": self.category,
            "subcategory": self.subcategory,
            "priority": self.priority,
            "sla_hours": self.sla_hours,
            "suggested_team": self.suggested_team,
            "triage_confidence": self.confidence
        }
