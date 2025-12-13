"""
Intent detection agent for SupportAI.

Analyzes customer messages to determine problem type and sentiment.
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


async def detect_intent(state: WorkflowState) -> WorkflowState:
    """
    Detect intent and sentiment from customer message.

    Args:
        state: Current workflow state

    Returns:
        Updated workflow state with intent information
    """
    try:
        logger.info(f"Detecting intent for ticket {state.get('ticket_id', 'unknown')}")

        # Initialize LLM
        llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0.1,  # Low temperature for consistent classification
            api_key=settings.openai_api_key
        )

        # Create prompt
        prompt = ChatPromptTemplate.from_template(get_prompt_template("intent_detection"))
        chain = prompt | llm

        # Get intent analysis
        ticket_text = state["original_message"]
        response = await chain.ainvoke({"ticket_text": ticket_text})

        # Parse JSON response
        try:
            intent_data = json.loads(response.content.strip())
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse intent detection response: {e}")
            # Fallback to default values
            intent_data = {
                "problem_type": "other",
                "sentiment": "neutral",
                "confidence": 0.5,
                "reasoning": "Failed to parse LLM response"
            }

        # Validate required fields
        required_fields = ["problem_type", "sentiment", "confidence"]
        for field in required_fields:
            if field not in intent_data:
                logger.warning(f"Missing field in intent data: {field}")
                intent_data[field] = "unknown" if field != "confidence" else 0.0

        # Update state
        state["intent"] = intent_data

        logger.info(f"Intent detected: {intent_data['problem_type']}, sentiment: {intent_data['sentiment']}")

        return state

    except Exception as e:
        logger.error(f"Intent detection failed: {str(e)}")
        state["errors"].append(f"Intent detection error: {str(e)}")

        # Set fallback values
        state["intent"] = {
            "problem_type": "other",
            "sentiment": "neutral",
            "confidence": 0.0,
            "reasoning": "Error during processing"
        }

        return state