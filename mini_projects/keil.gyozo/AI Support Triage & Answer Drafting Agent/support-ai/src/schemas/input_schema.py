"""
Pydantic schemas for SupportAI input validation.

Defines input models for ticket processing.
"""

from typing import Optional
from pydantic import BaseModel, Field, EmailStr


class TicketInput(BaseModel):
    """Input schema for support ticket processing."""

    ticket_id: str = Field(..., description="Unique ticket identifier")
    message: str = Field(..., min_length=1, description="Customer's message content")
    customer_email: Optional[EmailStr] = Field(None, description="Customer's email address")
    subject: Optional[str] = Field(None, description="Ticket subject line")
    channel: Optional[str] = Field("email", description="Source channel (email, chat, etc.)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "ticket_id": "TKT-2025-12-09-4567",
                "message": "Hi, I just noticed I was charged $49.99 TWICE...",
                "customer_email": "john.doe@example.com",
                "subject": "Charged twice for subscription!",
                "channel": "email"
            }
        }
    }