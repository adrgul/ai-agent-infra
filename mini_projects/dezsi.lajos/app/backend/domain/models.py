from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

# --- Chat / General Models ---

class Message(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    generated_ticket: Optional[Dict[str, Any]] = None

# --- Medical Agent Models ---

class TicketInput(BaseModel):
    message: str
    user_role: Optional[str] = "Medical Rep"
    system_info: Optional[str] = None

class Analysis(BaseModel):
    summary: str = Field(description="Brief summary of the issue")
    intent: str = Field(description="Detected intent, e.g., Technical Issue, Access Request")
    complexity: Literal["Low", "Medium", "High", "Critical"]

class TriageDecision(BaseModel):
    support_tier: Literal["Tier 1 Support", "Tier 2 Support", "Tier 3 Support", "Vendor Product Support"]
    responsible_party: str
    reasoning: str
    escalation_needed: bool

class AnswerDraft(BaseModel):
    recipient: str = "User"
    body: str
    citations: List[str] = []

class TicketOutput(BaseModel):
    ticket_id: str = Field(default_factory=lambda: f"INC-{datetime.now().year}-{str(uuid.uuid4())[:4]}")
    analysis: Analysis
    triage_decision: TriageDecision
    answer_draft: AnswerDraft
    ticket_created: Optional[Dict[str, Any]] = None

class TicketCreate(BaseModel):
    title: str = Field(description="Title of the ticket")
    description: str = Field(description="Detailed description")
    priority: Literal["Low", "Medium", "High", "Critical"]
    category: Optional[str] = Field(None, description="Category e.g., 'Bug', 'Access', 'Question'")
    tags: List[str] = []
