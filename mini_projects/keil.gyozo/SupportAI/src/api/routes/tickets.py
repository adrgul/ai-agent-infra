"""Ticket processing endpoints."""

import logging
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from ...models.ticket import TicketInput, TicketOutput
from ...models.state import SupportTicketState
from ...workflow import build_support_workflow
from ...services import QdrantService, EmbeddingService
from ...utils.metrics import Timer, metrics

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/tickets", tags=["tickets"])

# Global workflow instance (initialized on startup)
workflow = None
qdrant_service = None
embedding_service = None


def initialize_workflow() -> None:
    """Initialize workflow and services.

    This should be called during application startup.
    """
    global workflow, qdrant_service, embedding_service

    logger.info("Initializing workflow and services")

    qdrant_service = QdrantService()
    embedding_service = EmbeddingService()
    workflow = build_support_workflow(
        qdrant_service=qdrant_service,
        embedding_service=embedding_service
    )

    logger.info("Workflow initialized successfully")


class ProcessResponse(BaseModel):
    """Response for ticket processing endpoint."""

    success: bool
    ticket_id: str
    result: TicketOutput


@router.post(
    "/process",
    response_model=ProcessResponse,
    status_code=status.HTTP_200_OK,
    summary="Process a support ticket",
    description=(
        "Process an incoming support ticket through the AI triage and "
        "response generation workflow. Returns triage classification, "
        "draft response, and citations."
    )
)
async def process_ticket(ticket: TicketInput) -> ProcessResponse:
    """Process a support ticket through the workflow.

    This endpoint:
    1. Receives a customer support ticket
    2. Runs it through the LangGraph workflow
    3. Returns triage classification and draft response

    Args:
        ticket: Input ticket data

    Returns:
        Processing result with triage and draft response

    Raises:
        HTTPException: If processing fails
    """
    logger.info(f"Processing ticket: {ticket.ticket_id}")

    # Initialize workflow if not done
    if workflow is None:
        initialize_workflow()

    # Build initial state
    initial_state: SupportTicketState = {
        "ticket_id": ticket.ticket_id,
        "raw_message": ticket.raw_message,
        "customer_name": ticket.customer_name,
        "customer_email": ticket.customer_email
    }

    try:
        # Execute workflow with timing
        with Timer(f"ticket_processing_{ticket.ticket_id}"):
            result = await workflow.ainvoke(initial_state)

        # Extract output
        output_data = result.get("output")
        if not output_data:
            raise ValueError("Workflow did not produce output")

        # Validate output
        validated_output = TicketOutput(**output_data)

        # Record metrics
        metrics.increment_counter("tickets_processed")
        metrics.increment_counter(f"priority_{validated_output.triage.priority}")
        metrics.increment_counter(f"category_{validated_output.triage.category}")
        metrics.increment_counter(
            f"compliance_{validated_output.policy_check.compliance}"
        )

        logger.info(
            f"Ticket {ticket.ticket_id} processed successfully - "
            f"Priority: {validated_output.triage.priority}, "
            f"Category: {validated_output.triage.category}, "
            f"Compliance: {validated_output.policy_check.compliance}"
        )

        return ProcessResponse(
            success=True,
            ticket_id=ticket.ticket_id,
            result=validated_output
        )

    except Exception as e:
        logger.error(f"Failed to process ticket {ticket.ticket_id}: {e}", exc_info=True)
        metrics.increment_counter("tickets_failed")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ticket processing failed: {str(e)}"
        )


@router.get(
    "/metrics",
    summary="Get processing metrics",
    description="Retrieve current processing metrics and statistics"
)
async def get_metrics() -> dict:
    """Get current processing metrics.

    Returns:
        Metrics statistics including counters, timers, and gauges
    """
    return metrics.get_stats()
