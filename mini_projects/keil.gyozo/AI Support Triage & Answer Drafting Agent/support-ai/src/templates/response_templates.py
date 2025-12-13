"""
Response templates for different categories and scenarios.

Pre-defined response structures for common support scenarios.
"""

from typing import Dict, Any


# Response Templates by Category
RESPONSE_TEMPLATES = {
    "billing_invoice": {
        "greeting": "Dear {customer_name},",
        "body_template": """Thank you for bringing this billing issue to our attention. I understand how important it is to have accurate billing records.

Regarding your {issue_description}, our Finance team specializes in these matters and will investigate promptly.

What to expect:
• Review of your account within 24 hours
• Resolution typically within 3-5 business days
• Email notification once resolved

If you have any additional details or documentation, please reply to this ticket.

Best regards,
Support Team""",
        "tone": "professional_helpful"
    },

    "billing_refund": {
        "greeting": "Dear {customer_name},",
        "body_template": """I appreciate you letting us know about this billing discrepancy. Duplicate charges can be frustrating, and I want to assure you we'll look into this right away.

Our Finance team will:
1. Review your transaction history
2. Verify the charge details
3. Process any necessary adjustments
4. Notify you of the resolution

This process typically takes 3-5 business days. You'll receive an email confirmation once the review is complete.

Please let us know if there's anything else we can help with in the meantime.

Best regards,
Support Team""",
        "tone": "empathetic_professional"
    },

    "technical_login": {
        "greeting": "Dear {customer_name},",
        "body_template": """I'm sorry to hear you're having trouble accessing your account. Let's get you back in quickly.

To reset your password:
1. Visit our login page
2. Click "Forgot Password"
3. Enter your email address
4. Follow the instructions in the reset email

If you're still unable to access your account after resetting your password, please reply with:
• The exact error message you're seeing
• What device/browser you're using
• Any recent changes to your account

Our Technical team will assist you further if needed.

Best regards,
Support Team""",
        "tone": "helpful_supportive"
    },

    "account_access": {
        "greeting": "Dear {customer_name},",
        "body_template": """Thank you for reaching out about your account access. I understand how important it is to have reliable access to your services.

To help resolve this quickly, could you please provide:
• Your account email address
• The specific error or issue you're experiencing
• When this started happening
• Any recent changes you've made

Once we have this information, our Account team can investigate and get you back up and running.

In the meantime, you can also try:
• Clearing your browser cache and cookies
• Using a different browser or device
• Checking our status page for any ongoing issues

Best regards,
Support Team""",
        "tone": "professional_helpful"
    },

    "feature_request": {
        "greeting": "Dear {customer_name},",
        "body_template": """Thank you for your suggestion! We appreciate you taking the time to share your ideas for improving our service.

Your feedback about {feature_description} has been noted and will be reviewed by our Product team. We regularly review customer suggestions to help prioritize our development roadmap.

While we can't commit to specific timelines, your input helps us understand what features are most important to our users.

If you'd like to:
• Provide more details about your use case
• Share how this feature would help you
• See similar requests from other customers

Please feel free to reply to this ticket.

Thank you again for helping us improve!

Best regards,
Support Team""",
        "tone": "friendly_appreciative"
    }
}


def get_response_template(category: str, subcategory: str = None) -> Dict[str, Any]:
    """
    Get appropriate response template for category.

    Args:
        category: Main category
        subcategory: Optional subcategory for more specific templates

    Returns:
        Template dictionary with greeting, body_template, and tone
    """
    # Map categories to template keys
    category_mapping = {
        "Billing - Invoice Issue": "billing_invoice",
        "Billing - Refund": "billing_refund",
        "Technical - Login": "technical_login",
        "Account - Access": "account_access",
        "Feature Request": "feature_request",
    }

    template_key = category_mapping.get(category, "account_access")  # Default fallback

    return RESPONSE_TEMPLATES.get(template_key, RESPONSE_TEMPLATES["account_access"])


def format_response_template(
    template: Dict[str, Any],
    customer_name: str = "Customer",
    issue_description: str = "your issue",
    feature_description: str = "this feature"
) -> Dict[str, Any]:
    """
    Format template with customer-specific information.

    Args:
        template: Template dictionary
        customer_name: Customer's name
        issue_description: Description of the issue
        feature_description: Description of requested feature

    Returns:
        Formatted template
    """
    formatted = template.copy()

    # Format greeting
    formatted["greeting"] = template["greeting"].format(customer_name=customer_name)

    # Format body
    formatted["body_template"] = template["body_template"].format(
        customer_name=customer_name,
        issue_description=issue_description,
        feature_description=feature_description
    )

    return formatted


# Tone adjustment mappings
TONE_ADJUSTMENTS = {
    "frustrated": {
        "add_empathy": True,
        "use_apology": True,
        "be_reassuring": True,
        "keep_concise": False
    },
    "neutral": {
        "add_empathy": False,
        "use_apology": False,
        "be_reassuring": True,
        "keep_concise": True
    },
    "satisfied": {
        "add_empathy": False,
        "use_apology": False,
        "be_reassuring": False,
        "keep_concise": True
    }
}


def adjust_tone_for_sentiment(base_template: Dict[str, Any], sentiment: str) -> Dict[str, Any]:
    """
    Adjust response template based on customer sentiment.

    Args:
        base_template: Base template
        sentiment: Customer sentiment

    Returns:
        Adjusted template
    """
    adjustments = TONE_ADJUSTMENTS.get(sentiment, TONE_ADJUSTMENTS["neutral"])

    adjusted = base_template.copy()

    if adjustments["add_empathy"]:
        adjusted["body_template"] = f"I understand this can be frustrating. {adjusted['body_template']}"

    if adjustments["use_apology"]:
        adjusted["body_template"] = f"I'm sorry for the inconvenience. {adjusted['body_template']}"

    if adjustments["be_reassuring"]:
        adjusted["body_template"] += "\n\nRest assured we're here to help resolve this for you."

    return adjusted