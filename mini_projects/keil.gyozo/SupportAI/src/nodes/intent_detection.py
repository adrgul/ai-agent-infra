"""Intent detection node - classifies problem type and sentiment."""

import logging
from datetime import datetime, timezone

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from ..models.state import SupportTicketState
from ..services import get_llm

logger = logging.getLogger(__name__)


class IntentResult(BaseModel):
    """Structured output for intent detection."""

    problem_type: str = Field(
        ...,
        description="Problem type: billing | technical | account | feature_request"
    )
    sentiment: str = Field(
        ...,
        description="Customer sentiment: frustrated | neutral | satisfied"
    )
    urgency_keywords: list[str] = Field(
        default_factory=list,
        description="Detected urgency indicators"
    )


async def intent_detection_node(state: SupportTicketState) -> dict:
    """Detect problem type and customer sentiment.

    This is the first node in the workflow. It analyzes the customer's message
    to understand what type of problem they're experiencing and their emotional state.

    Args:
        state: Current workflow state containing raw_message

    Returns:
        Dictionary with problem_type and sentiment fields
    """
    logger.info(f"Detecting intent for ticket: {state.get('ticket_id')}")

    llm = get_llm(temperature=0)
    structured_llm = llm.with_structured_output(IntentResult)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert at analyzing customer support messages.

Your task is to identify:
1. **Problem Type**: What category does this issue fall into?
   - billing: Payment, charges, invoices, refunds, subscriptions
   - technical: Bugs, errors, performance, features not working
   - account: Login, password, profile, access issues
   - feature_request: New features, enhancements, suggestions

2. **Sentiment**: What is the customer's emotional state?
   - frustrated: Angry, upset, multiple issues, urgency language
   - neutral: Calm, matter-of-fact, just reporting an issue
   - satisfied: Positive, happy with service despite issue

3. **Urgency Keywords**: Look for words like "urgent", "immediately", "ASAP", "critical", etc.

Be objective and accurate. The sentiment detection will influence priority assignment."""),
        ("human", """Ticket ID: {ticket_id}
Customer: {customer_name}
Message: {message}

Analyze this support ticket and classify the problem type and sentiment.""")
    ])

    chain = prompt | structured_llm

    try:
        result = await chain.ainvoke({
            "ticket_id": state.get("ticket_id", "UNKNOWN"),
            "customer_name": state.get("customer_name", "Customer"),
            "message": state["raw_message"]
        })

        logger.info(
            f"Intent detected - Type: {result.problem_type}, "
            f"Sentiment: {result.sentiment}, "
            f"Urgency: {len(result.urgency_keywords)} keywords"
        )

        return {
            "problem_type": result.problem_type,
            "sentiment": result.sentiment,
            "processed_at": datetime.now(timezone.utc).isoformat()
        }

    except Exception as e:
        logger.error(f"Intent detection failed: {e}")
        # Provide safe defaults on failure
        return {
            "problem_type": "technical",
            "sentiment": "neutral",
            "errors": [f"Intent detection error: {str(e)}"]
        }
