"""Validation node - final output validation and formatting."""

import logging
from datetime import datetime, timezone

from ..models.state import SupportTicketState
from ..models.ticket import (
    TicketOutput,
    TriageOutput,
    AnswerDraft,
    CitationOutput,
    PolicyCheckOutput,
)

logger = logging.getLogger(__name__)


async def validation_node(state: SupportTicketState) -> dict:
    """Validate and format final output as structured JSON.

    This is the final node in the workflow. It:
    1. Validates all required fields are present
    2. Converts to output schema with Pydantic validation
    3. Adds metadata (timestamp, etc.)
    4. Returns structured JSON for API response

    Args:
        state: Complete workflow state with all processed fields

    Returns:
        Dictionary with validated 'output' field
    """
    logger.info(f"Validating output for ticket: {state.get('ticket_id')}")

    try:
        # Build triage output
        triage = TriageOutput(
            category=state["category"],
            subcategory=state["subcategory"],
            priority=state["priority"],
            sla_hours=state["sla_hours"],
            suggested_team=state["suggested_team"],
            sentiment=state["sentiment"],
            confidence=state["triage_confidence"]
        )

        # Build answer draft output
        draft_data = state.get("answer_draft", {})
        answer_draft = AnswerDraft(
            greeting=draft_data.get("greeting", "Hi,"),
            body=draft_data.get("body", ""),
            closing=draft_data.get("closing", "Best regards,\nSupport Team"),
            tone=draft_data.get("tone", "empathetic_professional")
        )

        # Build citations output
        citations_data = state.get("citations", [])
        citations = [
            CitationOutput(**citation) for citation in citations_data
        ]

        # Build policy check output
        policy_data = state.get("policy_check", {})
        policy_check = PolicyCheckOutput(
            refund_promise=policy_data.get("refund_promise", False),
            sla_mentioned=policy_data.get("sla_mentioned", False),
            escalation_needed=policy_data.get("escalation_needed", False),
            compliance=policy_data.get("compliance", "warning"),
            issues=policy_data.get("issues")
        )

        # Build complete output
        output = TicketOutput(
            ticket_id=state["ticket_id"],
            timestamp=datetime.now(timezone.utc).isoformat(),
            triage=triage,
            answer_draft=answer_draft,
            citations=citations,
            policy_check=policy_check
        )

        logger.info(
            f"Validation complete - Compliance: {policy_check.compliance}, "
            f"Citations: {len(citations)}, "
            f"Priority: {triage.priority}"
        )

        return {
            "output": output.model_dump()
        }

    except Exception as e:
        logger.error(f"Validation failed: {e}")

        # Try to build minimal valid output
        try:
            minimal_output = TicketOutput(
                ticket_id=state.get("ticket_id", "UNKNOWN"),
                timestamp=datetime.now(timezone.utc).isoformat(),
                triage=TriageOutput(
                    category=state.get("category", "Technical"),
                    subcategory=state.get("subcategory", "General Issue"),
                    priority=state.get("priority", "P3"),
                    sla_hours=state.get("sla_hours", 72),
                    suggested_team=state.get("suggested_team", "Support Team"),
                    sentiment=state.get("sentiment", "neutral"),
                    confidence=state.get("triage_confidence", 0.0)
                ),
                answer_draft=AnswerDraft(
                    greeting="Hi,",
                    body="We've received your support request and a specialist will review it shortly.",
                    closing="Best regards,\nSupport Team",
                    tone="empathetic_professional"
                ),
                citations=[],
                policy_check=PolicyCheckOutput(
                    refund_promise=False,
                    sla_mentioned=False,
                    escalation_needed=True,
                    compliance="failed",
                    issues=[f"Validation error: {str(e)}"]
                )
            )

            return {
                "output": minimal_output.model_dump(),
                "errors": [f"Validation error: {str(e)}"]
            }

        except Exception as fallback_error:
            logger.critical(f"Even fallback validation failed: {fallback_error}")
            raise
