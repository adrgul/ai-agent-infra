"""
Action Items node for extracting actionable tasks from meeting transcripts.

This node uses an LLM to identify and structure action items including
assignees, deadlines, and priorities.
"""

from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from src.models.schemas import GraphState, ActionItem


# System prompt for action items extraction
ACTION_ITEMS_SYSTEM_PROMPT = """You are an expert at extracting action items from meeting transcripts.

Your task is to identify all actionable tasks mentioned in the meeting and extract:
1. The specific task or action to be completed
2. Who is assigned to complete it (if mentioned)
3. Any deadline or due date mentioned (if specified)
4. Priority level (high, medium, or low based on context)

Guidelines:
- Only extract explicit action items, not general discussions
- Look for phrases like "will do", "should complete", "needs to", "action item", "todo", "by [date]"
- Infer priority from urgency indicators (ASAP, urgent, when possible, etc.)
- Be specific about the task description
- If assignee or deadline is unclear, use null
- If multiple people are assigned, list the primary person or use "Team"
"""


# User prompt template
ACTION_ITEMS_USER_PROMPT = """Extract all action items from the following meeting transcript.

Meeting Transcript:
{transcript}

Please provide your response in the following JSON format:
{{
    "action_items": [
        {{
            "task": "specific task description",
            "assignee": "person name or null",
            "deadline": "deadline string or null",
            "priority": "high, medium, or low"
        }}
    ]
}}

If there are no action items, return an empty list.
Ensure each action item is clear, specific, and actionable."""


def create_action_items_chain(llm: ChatOpenAI):
    """
    Create the action items extraction LangChain chain.

    Args:
        llm: The ChatOpenAI language model instance

    Returns:
        A LangChain chain for extracting action items
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", ACTION_ITEMS_SYSTEM_PROMPT),
        ("user", ACTION_ITEMS_USER_PROMPT)
    ])

    # We'll parse the list of action items
    output_parser = JsonOutputParser()

    chain = prompt | llm | output_parser

    return chain


def extract_action_items(state: GraphState, llm: ChatOpenAI) -> Dict[str, Any]:
    """
    Extract action items from the meeting transcript.

    This node uses an LLM to identify and structure actionable tasks
    with assignees, deadlines, and priorities.

    Args:
        state: The current graph state with parsed transcript
        llm: The ChatOpenAI language model instance

    Returns:
        Dict with updated state containing action items
    """
    transcript = state.parsed_transcript or state.transcript

    try:
        # Create the chain
        chain = create_action_items_chain(llm)

        # Invoke the chain
        result = chain.invoke({"transcript": transcript})

        # Parse action items
        action_items_data = result.get("action_items", [])

        # Convert to ActionItem models with validation
        action_items: List[ActionItem] = []
        for item_data in action_items_data:
            try:
                action_item = ActionItem(**item_data)
                action_items.append(action_item)
            except Exception as e:
                # Log validation error but continue with other items
                error_msg = f"Action item validation error: {str(e)}"
                state.errors.append(error_msg)

        return {
            "action_items": action_items,
            "errors": state.errors
        }

    except Exception as e:
        error_msg = f"Action items extraction error: {str(e)}"
        return {
            "action_items": [],
            "errors": state.errors + [error_msg]
        }
