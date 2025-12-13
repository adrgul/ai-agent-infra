"""
LLM prompt templates for SupportAI agents.

Contains all prompts used by the various agent nodes.
"""

from typing import Dict, Any


# Intent Detection Prompts
INTENT_DETECTION_PROMPT = """
Analyze the following customer support ticket and determine:

1. Problem Type: Classify into one of: billing, technical, account, feature_request, other
2. Sentiment: Classify as: frustrated, neutral, satisfied

Ticket:
{ticket_text}

Respond with a JSON object containing:
- "problem_type": "billing|technical|account|feature_request|other"
- "sentiment": "frustrated|neutral|satisfied"
- "confidence": 0.0-1.0
- "reasoning": brief explanation

Examples:
- "Charged twice for subscription" → billing, frustrated
- "How do I reset my password?" → account, neutral
- "Love the new feature!" → feature_request, satisfied
"""

# Triage Classification Prompts
TRIAGE_CLASSIFICATION_PROMPT = """
Classify this support ticket for routing and prioritization.

Problem Type: {problem_type}
Sentiment: {sentiment}
Ticket: {ticket_text}

Determine:
1. Category: Choose from standard categories
2. Subcategory: More specific classification
3. Priority: P1 (Critical), P2 (Medium), P3 (Low)
4. SLA Hours: Response time commitment
5. Suggested Team: Which team should handle this

Priority Guidelines:
- P1: Account locked, payment failures, security issues, urgent outages
- P2: Billing issues, feature bugs, account changes
- P3: General questions, documentation requests, minor issues

Category Examples:
- Billing: Invoice Issues, Payment Methods, Refunds
- Technical: Login Problems, Feature Bugs, Performance
- Account: Password Reset, Profile Updates, Access Issues
- Feature: New Features, Improvements, Integrations

Respond with JSON:
{{
  "category": "string",
  "subcategory": "string",
  "priority": "P1|P2|P3",
  "sla_hours": number,
  "suggested_team": "string",
  "confidence": 0.0-1.0
}}
"""

# Query Expansion Prompts
QUERY_EXPANSION_PROMPT = """
Generate 3-5 semantic search queries for finding relevant knowledge base articles.

Original ticket: {ticket_text}
Problem type: {problem_type}
Category: {category}

Create diverse queries that would help find relevant documentation:
- Expand abbreviations (e.g., "txn" → "transaction")
- Add synonyms (e.g., "charge" → "billing", "payment")
- Create specific + general variations
- Include technical terms and common phrases

Respond with a JSON array of strings, each 3-10 words long.

Examples for "duplicate charge":
["duplicate subscription charge", "double billing issue", "refund duplicate payment", "invoice error multiple charges"]
"""

# Draft Generation Prompts
DRAFT_GENERATION_PROMPT = """
Generate a personalized customer support response draft.

Ticket: {ticket_text}
Customer: {customer_name}
Category: {category}
Priority: {priority}
Sentiment: {sentiment}
Suggested Team: {suggested_team}

Available Knowledge Base Articles:
{kb_articles}

Response Guidelines:
1. Greeting: Use customer's name if available, otherwise "Dear Customer"
2. Empathy: Acknowledge the issue, especially if frustrated
3. Solution: Provide clear steps using KB articles
4. Citations: Reference articles as [KB-1234], [FAQ-567]
5. Timeline: Mention expected resolution time
6. Closing: Professional sign-off

Tone Guidelines:
- frustrated: empathetic, apologetic, reassuring
- neutral: professional, helpful, informative
- satisfied: friendly, encouraging, positive

Keep response concise but comprehensive. Include next steps for customer.

Response Structure:
{{
  "greeting": "string",
  "body": "string with citations",
  "closing": "string",
  "tone": "string"
}}
"""

# Policy Check Prompts
POLICY_CHECK_PROMPT = """
Review this response draft for company policy compliance.

Draft Response:
{draft}

Check for:
1. Refund Promises: Does it promise refunds or credits?
2. SLA Guarantees: Does it guarantee specific resolution times?
3. Escalation Triggers: Does it indicate need for human review?

Policy Rules:
- NEVER promise refunds without approval
- Use "typically" or "generally" instead of guarantees
- Escalate: legal threats, account closure threats, complex technical issues

Respond with JSON:
{{
  "refund_promise": boolean,
  "sla_mentioned": boolean,
  "escalation_needed": boolean,
  "compliance": "passed|failed",
  "violations": ["list of violations"]
}}
"""

# Re-ranking Prompts
RERANKING_PROMPT = """
Given a query and a list of documents, score each document's relevance from 0-10.

Query: {query}

Documents:
{documents}

For each document, provide:
- Relevance score (0-10, where 10 is perfectly relevant)
- Brief reasoning

Respond with JSON array of objects:
[{{"doc_id": "id", "score": 8.5, "reasoning": "explanation"}}]
"""


def get_prompt_template(template_name: str, **kwargs) -> str:
    """
    Get formatted prompt template.

    Args:
        template_name: Name of the prompt template
        **kwargs: Template variables

    Returns:
        Formatted prompt string
    """
    templates = {
        "intent_detection": INTENT_DETECTION_PROMPT,
        "triage_classification": TRIAGE_CLASSIFICATION_PROMPT,
        "query_expansion": QUERY_EXPANSION_PROMPT,
        "draft_generation": DRAFT_GENERATION_PROMPT,
        "policy_check": POLICY_CHECK_PROMPT,
        "reranking": RERANKING_PROMPT,
    }

    template = templates.get(template_name)
    if not template:
        raise ValueError(f"Unknown prompt template: {template_name}")

    return template.format(**kwargs)