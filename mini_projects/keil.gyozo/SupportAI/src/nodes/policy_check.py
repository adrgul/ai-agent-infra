"""Policy check node - validates draft against business rules.

⚠️ IMPORTANT: This node is named "check_policy" in the workflow graph
to avoid collision with the state field "policy_check".
"""

import logging
import re

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from ..models.state import SupportTicketState
from ..services import get_llm

logger = logging.getLogger(__name__)


class PolicyCheckResult(BaseModel):
    """Structured output for policy compliance check."""

    refund_promise: bool = Field(
        ...,
        description="True if draft promises a refund (requires manager approval)"
    )
    sla_mentioned: bool = Field(
        ...,
        description="True if specific SLA/timeline is mentioned"
    )
    escalation_needed: bool = Field(
        ...,
        description="True if issue requires escalation to specialist"
    )
    compliance: str = Field(
        ...,
        description="Overall compliance: passed | warning | failed"
    )
    issues: list[str] = Field(
        default_factory=list,
        description="List of compliance issues found"
    )


async def policy_check_node(state: SupportTicketState) -> dict:
    """Validate draft response against company policies and business rules.

    This node ensures that automated responses:
    - Don't make unauthorized promises (refunds, credits, exceptions)
    - Don't commit to specific SLAs without authorization
    - Properly escalate complex issues
    - Follow company tone and style guidelines
    - Don't include sensitive information

    Compliance levels:
    - passed: No issues, safe to send
    - warning: Minor issues, review recommended
    - failed: Critical issues, human review required

    Args:
        state: Current workflow state with answer_draft

    Returns:
        Dictionary with policy_check results
    """
    logger.info(f"Checking policy compliance for ticket: {state.get('ticket_id')}")

    answer_draft = state.get("answer_draft", {})
    if not answer_draft:
        logger.warning("No answer draft to check")
        return {
            "policy_check": {
                "refund_promise": False,
                "sla_mentioned": False,
                "escalation_needed": False,
                "compliance": "failed",
                "issues": ["No answer draft available"]
            }
        }

    # Combine draft parts for analysis
    full_response = f"{answer_draft.get('body', '')} {answer_draft.get('closing', '')}"

    llm = get_llm(temperature=0)
    structured_llm = llm.with_structured_output(PolicyCheckResult)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a compliance officer reviewing automated support responses.

**Check for these policy violations:**

1. **Refund Promises** - Requires manager approval:
   - Direct promises: "we will refund", "you'll receive a refund"
   - Credits or compensation promises
   - Flag as violation unless: "may be eligible", "we'll review"

2. **SLA Commitments** - Specific timeframes require authorization:
   - "within 24 hours", "by tomorrow", "same day"
   - OK: "within our standard timeframe", "as quickly as possible"

3. **Escalation Needed** - Complex issues requiring specialist:
   - Legal matters, security breaches, privacy requests
   - Multiple unresolved issues
   - Customer explicitly requested escalation

4. **Other Violations:**
   - Sharing internal processes or system details
   - Making exceptions to standard policy
   - Guarantees of specific outcomes

**Compliance Levels:**
- passed: No violations found
- warning: Minor issues, suggest review (1-2 soft violations)
- failed: Critical violations, human review required"""),
        ("human", """Category: {category}
Priority: {priority}
Sentiment: {sentiment}

Draft Response:
{response}

Check this response for policy compliance.""")
    ])

    chain = prompt | structured_llm

    try:
        result = await chain.ainvoke({
            "category": state.get("category", "General"),
            "priority": state.get("priority", "P3"),
            "sentiment": state.get("sentiment", "neutral"),
            "response": full_response
        })

        # Additional heuristic checks (in case LLM misses obvious patterns)
        refund_keywords = [
            "will refund", "we'll refund", "refund you", "issue a refund",
            "provide a credit", "compensate you"
        ]
        for keyword in refund_keywords:
            if keyword.lower() in full_response.lower() and not result.refund_promise:
                logger.warning(f"Heuristic detected refund promise: '{keyword}'")
                result.refund_promise = True
                if "Unauthorized refund promise detected" not in result.issues:
                    result.issues.append("Unauthorized refund promise detected")

        # Check for specific time commitments
        time_pattern = r'\b(within|in|by)\s+(\d+)\s+(hour|day|minute|week)s?\b'
        if re.search(time_pattern, full_response, re.IGNORECASE) and not result.sla_mentioned:
            logger.warning("Heuristic detected specific SLA mention")
            result.sla_mentioned = True
            result.issues.append("Specific SLA timeframe mentioned")

        # Escalation for P1 tickets
        if state.get("priority") == "P1" and not result.escalation_needed:
            result.escalation_needed = True
            result.issues.append("P1 ticket should be escalated to specialist")

        # Re-evaluate compliance based on all checks
        if result.refund_promise or (result.escalation_needed and state.get("priority") == "P1"):
            result.compliance = "failed"
        elif result.issues:
            result.compliance = "warning"
        else:
            result.compliance = "passed"

        logger.info(
            f"Policy check complete - Compliance: {result.compliance}, "
            f"Issues: {len(result.issues)}, "
            f"Refund: {result.refund_promise}, SLA: {result.sla_mentioned}, "
            f"Escalation: {result.escalation_needed}"
        )

        return {
            "policy_check": result.model_dump()
        }

    except Exception as e:
        logger.error(f"Policy check failed: {e}")
        # Fail-safe: mark as requiring review
        return {
            "policy_check": {
                "refund_promise": False,
                "sla_mentioned": False,
                "escalation_needed": True,
                "compliance": "failed",
                "issues": [f"Policy check error: {str(e)}"]
            }
        }
