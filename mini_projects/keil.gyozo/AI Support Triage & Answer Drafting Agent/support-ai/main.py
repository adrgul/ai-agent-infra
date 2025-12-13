#!/usr/bin/env python3
"""
SupportAI - AI-powered customer support triage and response agent

Main entry point for processing support tickets through the LangGraph workflow.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.workflow.langgraph_flow import create_support_workflow
from src.schemas.output_schema import SupportAgentOutput
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def process_ticket(
    ticket_id: str,
    message: str,
    customer_email: str | None = None
) -> SupportAgentOutput:
    """
    Process a single support ticket through the complete workflow.

    Args:
        ticket_id: Unique identifier for the ticket
        message: The customer's message/ticket content
        customer_email: Customer's email address (optional)

    Returns:
        SupportAgentOutput: Structured output with triage, draft, citations, and policy check
    """
    try:
        logger.info(f"Processing ticket {ticket_id}")

        # Create and compile the workflow
        workflow = create_support_workflow()

        # Initialize workflow state
        initial_state = {
            "ticket_id": ticket_id,
            "original_message": message,
            "customer_email": customer_email,
            "errors": []
        }

        # Execute the workflow
        result = await workflow.ainvoke(initial_state)

        # Validate and return structured output
        if "final_output" not in result:
            raise ValueError("Workflow did not produce final_output")

        output = SupportAgentOutput(**result["final_output"])
        logger.info(f"Successfully processed ticket {ticket_id}")

        return output

    except Exception as e:
        logger.error(f"Failed to process ticket {ticket_id}: {str(e)}")
        raise


def main():
    """Main CLI entry point."""
    # Example usage
    sample_ticket = """
    From: john.doe@example.com
    Subject: Charged twice for December subscription!

    Hi, I just noticed I was charged $49.99 TWICE on December 5th
    for my subscription. This is ridiculous! I want a refund immediately.
    My transaction ID is TXN-12345678.
    """

    try:
        result = asyncio.run(process_ticket(
            ticket_id="TKT-2025-12-09-4567",
            message=sample_ticket,
            customer_email="john.doe@example.com"
        ))

        print("=== SupportAI Output ===")
        print(result.model_dump_json(indent=2))

    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()