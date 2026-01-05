"""Draft answer node - generates response with citations."""

import logging
import re

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from ..models.state import SupportTicketState
from ..models.ticket import AnswerDraft
from ..models.rag import Citation
from ..services import get_llm

logger = logging.getLogger(__name__)


class DraftWithCitations(BaseModel):
    """Structured output for answer draft with inline citations."""

    greeting: str = Field(..., description="Personalized greeting")
    body: str = Field(
        ...,
        description="Response body with [DOC-ID] citations inline"
    )
    closing: str = Field(..., description="Professional closing")
    tone: str = Field(
        default="empathetic_professional",
        description="Response tone"
    )


async def draft_answer_node(state: SupportTicketState) -> dict:
    """Generate draft response with citations from knowledge base.

    This node creates a customer-facing response that:
    - Addresses the customer's question directly
    - Uses information from retrieved knowledge base articles
    - Includes inline citations [DOC-ID] for fact verification
    - Matches tone to customer sentiment
    - Follows company style guidelines

    Citation format: [DOC-ID] where DOC-ID is from the knowledge base
    Example: "Refunds typically take 5-7 business days [KB-1234]."

    Args:
        state: Current workflow state with reranked_docs and customer info

    Returns:
        Dictionary with answer_draft and citations
    """
    logger.info(f"Drafting answer for ticket: {state.get('ticket_id')}")

    reranked_docs = state.get("reranked_docs", [])
    if not reranked_docs:
        logger.warning("No reranked documents available for context")
        # Still try to generate an answer, but it will be generic

    # Build context from documents
    context_parts = []
    for i, doc in enumerate(reranked_docs[:3], 1):  # Use top 3
        context_parts.append(
            f"[{doc['doc_id']}] {doc['title']}\n{doc['content'][:300]}...\n"
        )
    context = "\n".join(context_parts) if context_parts else "No specific documentation available."

    # Determine tone based on sentiment
    sentiment = state.get("sentiment", "neutral")
    tone_guidance = {
        "frustrated": "Empathetic and apologetic. Acknowledge their frustration. Be solution-focused.",
        "neutral": "Professional and helpful. Direct and informative.",
        "satisfied": "Friendly and positive. Build on their satisfaction."
    }
    tone_instruction = tone_guidance.get(sentiment, tone_guidance["neutral"])

    llm = get_llm(temperature=0.3)  # Slightly creative for natural language
    structured_llm = llm.with_structured_output(DraftWithCitations)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a professional customer support agent drafting responses.

**Guidelines:**
1. Address the customer by name in the greeting
2. Acknowledge their specific issue
3. Provide clear, actionable information from the knowledge base
4. Include citations [DOC-ID] after each fact from documentation
5. Be concise but complete (150-300 words for body)
6. Use appropriate tone based on customer sentiment
7. End with a professional closing

**Citation Rules:**
- Put [DOC-ID] immediately after facts from knowledge base
- Example: "Refunds take 5-7 business days [KB-1234]."
- Don't cite for general statements or greetings
- Use the exact DOC-ID from the provided context

**Tone:** {tone_instruction}

**Available Knowledge Base Articles:**
{context}

If the knowledge base doesn't have relevant information, politely say you'll escalate
to a specialist who can provide detailed assistance."""),
        ("human", """Customer: {customer_name}
Email: {customer_email}
Sentiment: {sentiment}
Category: {category}
Message: {message}

Draft a helpful response to this customer.""")
    ])

    chain = prompt | structured_llm

    try:
        result = await chain.ainvoke({
            "customer_name": state.get("customer_name", "Customer"),
            "customer_email": state.get("customer_email", ""),
            "sentiment": sentiment,
            "category": state.get("category", "General"),
            "message": state["raw_message"],
            "tone_instruction": tone_instruction,
            "context": context
        })

        # Extract citations from the response body
        citation_pattern = r'\[(KB-\d+|FAQ-\d+|POLICY-\d+)\]'
        cited_doc_ids = re.findall(citation_pattern, result.body)

        # Build citation list
        citations = []
        for doc in reranked_docs:
            if doc["doc_id"] in cited_doc_ids:
                citation = Citation(
                    doc_id=doc["doc_id"],
                    chunk_id=doc["chunk_id"],
                    title=doc["title"],
                    score=doc["final_score"],
                    url=doc["url"]
                )
                citations.append(citation.model_dump())

        logger.info(
            f"Draft generated - {len(result.body)} chars, "
            f"{len(citations)} citations, tone: {result.tone}"
        )

        answer_draft = AnswerDraft(
            greeting=result.greeting,
            body=result.body,
            closing=result.closing,
            tone=result.tone
        )

        return {
            "answer_draft": answer_draft.model_dump(),
            "citations": citations
        }

    except Exception as e:
        logger.error(f"Draft generation failed: {e}")
        # Provide a generic error response
        fallback_draft = AnswerDraft(
            greeting=f"Hi {state.get('customer_name', 'there')},",
            body=(
                "Thank you for contacting support. We're experiencing a technical issue "
                "with our automated response system. A support specialist will review your "
                "case and respond within our standard SLA timeframe."
            ),
            closing="Best regards,\nSupport Team",
            tone="empathetic_professional"
        )

        return {
            "answer_draft": fallback_draft.model_dump(),
            "citations": [],
            "errors": [f"Draft generation error: {str(e)}"]
        }
