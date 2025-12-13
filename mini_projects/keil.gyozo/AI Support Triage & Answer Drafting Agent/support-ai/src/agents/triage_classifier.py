"""
Triage classification agent for SupportAI.

Classifies tickets by category, priority, SLA, and team assignment.
"""

import json
from typing import Dict, Any

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from ..workflow.state import WorkflowState
from ..utils.config import settings
from ..utils.logger import get_logger
from ..templates.prompts import get_prompt_template

logger = get_logger(__name__)


async def classify_triage(state: WorkflowState) -> WorkflowState:
    """
    Classify ticket for triage routing and prioritization.

    Args:
        state: Current workflow state

    Returns:
        Updated workflow state with triage information
    """
    try:
        logger.info(f"Classifying triage for ticket {state.get('ticket_id', 'unknown')}")

        # Get intent data from previous step
        intent = state.get("intent", {})
        problem_type = intent.get("problem_type", "other")
        sentiment = intent.get("sentiment", "neutral")

        # Initialize LLM
        llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0.1,  # Consistent classification
            api_key=settings.openai_api_key
        )

        # Create prompt
        prompt = ChatPromptTemplate.from_template(get_prompt_template("triage_classification"))
        chain = prompt | llm

        # Get triage classification
        ticket_text = state["original_message"]
        response = await chain.ainvoke({
            "problem_type": problem_type,
            "sentiment": sentiment,
            "ticket_text": ticket_text
        })

        # Parse JSON response
        try:
            triage_data = json.loads(response.content.strip())
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse triage classification response: {e}")
            # Fallback classification based on problem type
            triage_data = get_fallback_triage(problem_type, sentiment)

        # Validate required fields
        required_fields = ["category", "subcategory", "priority", "sla_hours", "suggested_team", "confidence"]
        for field in required_fields:
            if field not in triage_data:
                logger.warning(f"Missing field in triage data: {field}")
                triage_data[field] = get_default_value(field)

        # Validate priority levels
        if triage_data["priority"] not in ["P1", "P2", "P3"]:
            logger.warning(f"Invalid priority: {triage_data['priority']}, defaulting to P2")
            triage_data["priority"] = "P2"

        # Validate SLA hours
        if not isinstance(triage_data["sla_hours"], int) or triage_data["sla_hours"] < 1:
            triage_data["sla_hours"] = 24  # Default 24 hours

        # Update state
        state["triage"] = triage_data

        logger.info(f"Triage classified: {triage_data['category']} ({triage_data['priority']}) -> {triage_data['suggested_team']}")

        return state

    except Exception as e:
        logger.error(f"Triage classification failed: {str(e)}")
        state["errors"].append(f"Triage classification error: {str(e)}")

        # Set fallback triage
        state["triage"] = get_fallback_triage("other", "neutral")

        return state


def get_fallback_triage(problem_type: str, sentiment: str) -> Dict[str, Any]:
    """
    Get fallback triage classification when LLM fails.

    Args:
        problem_type: Detected problem type
        sentiment: Detected sentiment

    Returns:
        Fallback triage data
    """
    # Default mappings
    type_mapping = {
        "billing": {
            "category": "Billing - Invoice Issue",
            "subcategory": "General Billing",
            "suggested_team": "Finance Team",
            "priority": "P2",
            "sla_hours": 24
        },
        "technical": {
            "category": "Technical - General",
            "subcategory": "Technical Issue",
            "suggested_team": "Technical Team",
            "priority": "P2",
            "sla_hours": 24
        },
        "account": {
            "category": "Account - Access",
            "subcategory": "Account Issue",
            "suggested_team": "Account Team",
            "priority": "P2",
            "sla_hours": 24
        },
        "feature_request": {
            "category": "Feature Request",
            "subcategory": "New Feature",
            "suggested_team": "Product Team",
            "priority": "P3",
            "sla_hours": 48
        },
        "other": {
            "category": "General Inquiry",
            "subcategory": "General Question",
            "suggested_team": "Support Team",
            "priority": "P2",
            "sla_hours": 24
        }
    }

    base_triage = type_mapping.get(problem_type, type_mapping["other"])

    # Adjust priority based on sentiment
    if sentiment == "frustrated":
        base_triage["priority"] = "P1"
        base_triage["sla_hours"] = 4

    return {
        **base_triage,
        "confidence": 0.5  # Lower confidence for fallback
    }


def get_default_value(field: str) -> Any:
    """Get default value for missing triage field."""
    defaults = {
        "category": "General Inquiry",
        "subcategory": "General Question",
        "priority": "P2",
        "sla_hours": 24,
        "suggested_team": "Support Team",
        "confidence": 0.0
    }
    return defaults.get(field, "unknown")