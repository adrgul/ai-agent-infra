"""
Policy checker agent for SupportAI.

Validates response drafts against company policies.
"""

import json
from typing import Dict, Any

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from ..workflow.state import WorkflowState
from ..utils.config import settings
from ..utils.logger import get_logger
from ..templates.prompts import get_prompt_template
from ..utils.validators import check_policy_violations

logger = get_logger(__name__)


async def check_policies(state: WorkflowState) -> WorkflowState:
    """
    Check draft response for policy compliance.

    Args:
        state: Current workflow state

    Returns:
        Updated workflow state with policy check results
    """
    try:
        logger.info(f"Checking policies for ticket {state.get('ticket_id', 'unknown')}")

        # Get draft from previous step
        draft = state.get("draft", {})
        draft_text = f"{draft.get('greeting', '')}\n\n{draft.get('body', '')}\n\n{draft.get('closing', '')}"

        # Rule-based policy checks (fast and reliable)
        rule_based_checks = check_policy_violations(draft_text)

        # LLM-based policy validation for complex cases
        llm_checks = await perform_llm_policy_check(draft_text)

        # Combine results
        policy_check = {
            "refund_promise": rule_based_checks.get("refund_promise", False) or llm_checks.get("refund_promise", False),
            "sla_mentioned": rule_based_checks.get("sla_mentioned", False) or llm_checks.get("sla_mentioned", False),
            "escalation_needed": rule_based_checks.get("escalation_needed", False) or llm_checks.get("escalation_needed", False),
            "compliance": "passed" if not any([
                rule_based_checks.get("refund_promise", False),
                rule_based_checks.get("escalation_needed", False),
                llm_checks.get("compliance", "passed") == "failed"
            ]) else "failed",
            "violations": rule_based_checks.get("escalation_triggers", []) + llm_checks.get("violations", [])
        }

        # Update state
        state["policy_check"] = policy_check

        logger.info(f"Policy check completed: {policy_check['compliance']}")

        return state

    except Exception as e:
        logger.error(f"Policy check failed: {str(e)}")
        state["errors"].append(f"Policy check error: {str(e)}")

        # Set safe defaults
        state["policy_check"] = {
            "refund_promise": False,
            "sla_mentioned": False,
            "escalation_needed": True,  # Escalate on error
            "compliance": "failed",
            "violations": ["Policy check failed - manual review required"]
        }

        return state


async def perform_llm_policy_check(draft_text: str) -> Dict[str, Any]:
    """
    Use LLM for complex policy validation.

    Args:
        draft_text: Full draft text

    Returns:
        LLM-based policy check results
    """
    try:
        # Initialize LLM
        llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0.0,  # Deterministic for policy checks
            api_key=settings.openai_api_key
        )

        # Create prompt
        prompt = ChatPromptTemplate.from_template(get_prompt_template("policy_check"))
        chain = prompt | llm

        # Get policy validation
        response = await chain.ainvoke({"draft": draft_text})

        # Parse JSON response
        try:
            policy_data = json.loads(response.content.strip())
        except json.JSONDecodeError:
            logger.warning("Failed to parse LLM policy check response, using defaults")
            return {
                "refund_promise": False,
                "sla_mentioned": False,
                "escalation_needed": False,
                "compliance": "passed",
                "violations": []
            }

        return policy_data

    except Exception as e:
        logger.error(f"LLM policy check failed: {str(e)}")
        return {
            "refund_promise": False,
            "sla_mentioned": False,
            "escalation_needed": False,
            "compliance": "passed",
            "violations": []
        }