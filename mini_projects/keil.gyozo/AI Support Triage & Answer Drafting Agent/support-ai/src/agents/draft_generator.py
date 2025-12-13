"""
Draft generation agent for SupportAI.

Creates personalized response drafts with citations.
"""

import json
from typing import Dict, Any, List

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from ..workflow.state import WorkflowState
from ..utils.config import settings
from ..utils.logger import get_logger
from ..templates.prompts import get_prompt_template
from ..templates.response_templates import get_response_template, format_response_template, adjust_tone_for_sentiment

logger = get_logger(__name__)


async def generate_draft(state: WorkflowState) -> WorkflowState:
    """
    Generate personalized response draft with citations.

    Args:
        state: Current workflow state

    Returns:
        Updated workflow state with draft response
    """
    try:
        logger.info(f"Generating draft for ticket {state.get('ticket_id', 'unknown')}")

        # Get context from previous steps
        intent = state.get("intent", {})
        triage = state.get("triage", {})
        reranked_docs = state.get("reranked_docs", [])

        sentiment = intent.get("sentiment", "neutral")
        category = triage.get("category", "General Inquiry")
        priority = triage.get("priority", "P2")
        suggested_team = triage.get("suggested_team", "Support Team")

        # Get customer name
        customer_email = state.get("customer_email")
        customer_name = extract_customer_name(customer_email) if customer_email else "Customer"

        # Format knowledge base articles for prompt
        kb_articles = format_kb_articles(reranked_docs)

        # Initialize LLM
        llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0.2,  # Balanced creativity and consistency
            api_key=settings.openai_api_key
        )

        # Create prompt
        prompt = ChatPromptTemplate.from_template(get_prompt_template("draft_generation"))
        chain = prompt | llm

        # Generate draft
        ticket_text = state["original_message"]
        response = await chain.ainvoke({
            "ticket_text": ticket_text,
            "customer_name": customer_name,
            "category": category,
            "priority": priority,
            "sentiment": sentiment,
            "suggested_team": suggested_team,
            "kb_articles": kb_articles
        })

        # Parse JSON response
        try:
            draft_data = json.loads(response.content.strip())
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse draft generation response: {e}")
            # Fallback to template-based generation
            draft_data = generate_template_draft(
                customer_name, category, sentiment, reranked_docs, triage
            )

        # Validate required fields
        required_fields = ["greeting", "body", "closing", "tone"]
        for field in required_fields:
            if field not in draft_data:
                logger.warning(f"Missing field in draft data: {field}")
                draft_data[field] = get_default_draft_value(field)

        # Update state
        state["draft"] = draft_data

        logger.info(f"Draft generated with tone: {draft_data['tone']}")

        return state

    except Exception as e:
        logger.error(f"Draft generation failed: {str(e)}")
        state["errors"].append(f"Draft generation error: {str(e)}")

        # Set fallback draft
        state["draft"] = generate_template_draft("Customer", "General", "neutral", [], {})

        return state


def format_kb_articles(reranked_docs: List[Dict[str, Any]]) -> str:
    """
    Format knowledge base articles for prompt inclusion.

    Args:
        reranked_docs: List of reranked documents

    Returns:
        Formatted string of articles
    """
    if not reranked_docs:
        return "No relevant knowledge base articles found."

    formatted = []
    for i, doc in enumerate(reranked_docs[:5]):  # Top 5 articles
        title = doc.get("title", "Untitled")
        content = doc.get("content", "")[:500]  # Truncate content
        doc_id = doc.get("doc_id", f"doc-{i}")
        score = doc.get("score", 0.0)

        formatted.append(f"[{doc_id}] {title} (relevance: {score:.2f})\n{content}...")

    return "\n\n".join(formatted)


def extract_customer_name(email: str) -> str:
    """
    Extract customer name from email address.

    Args:
        email: Customer email

    Returns:
        Extracted name or "Customer"
    """
    if not email or "@" not in email:
        return "Customer"

    local_part = email.split("@")[0]

    # Handle common email formats
    if "." in local_part:
        parts = local_part.split(".")
        # Capitalize each part
        name_parts = [part.capitalize() for part in parts if len(part) > 1]
        if name_parts:
            return " ".join(name_parts)

    # Fallback: capitalize and clean
    name = local_part.replace("_", " ").replace("-", " ").title()
    return name if len(name) > 1 else "Customer"


def generate_template_draft(
    customer_name: str,
    category: str,
    sentiment: str,
    reranked_docs: List[Dict[str, Any]],
    triage: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate draft using response templates as fallback.

    Args:
        customer_name: Customer name
        category: Ticket category
        sentiment: Customer sentiment
        reranked_docs: Available KB articles
        triage: Triage information

    Returns:
        Draft data dictionary
    """
    # Get base template
    template = get_response_template(category)

    # Adjust for sentiment
    adjusted_template = adjust_tone_for_sentiment(template, sentiment)

    # Format with customer data
    formatted = format_response_template(
        adjusted_template,
        customer_name=customer_name,
        issue_description="your inquiry"
    )

    # Add citations if available
    body = formatted["body_template"]
    if reranked_docs:
        citations = [f"[{doc.get('doc_id', 'KB-000')}]" for doc in reranked_docs[:3]]
        body += f"\n\nFor more information, please see: {' '.join(citations)}"

    return {
        "greeting": formatted["greeting"],
        "body": body,
        "closing": "Best regards,\nSupport Team",
        "tone": adjusted_template["tone"]
    }


def get_default_draft_value(field: str) -> str:
    """Get default value for missing draft field."""
    defaults = {
        "greeting": "Dear Customer,",
        "body": "Thank you for your inquiry. We're reviewing your request and will get back to you soon.",
        "closing": "Best regards,\nSupport Team",
        "tone": "professional"
    }
    return defaults.get(field, "")