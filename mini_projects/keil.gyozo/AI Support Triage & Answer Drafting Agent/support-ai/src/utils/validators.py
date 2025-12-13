"""
Validation utilities for SupportAI.

Schema validation, policy checking, and input sanitization.
"""

import re
from typing import List, Dict, Any
from pathlib import Path

from .logger import get_logger

logger = get_logger(__name__)


def validate_file_path(file_path: str, allowed_extensions: List[str] = None) -> bool:
    """
    Validate file path exists and has allowed extension.

    Args:
        file_path: Path to validate
        allowed_extensions: List of allowed extensions (e.g., ['.txt', '.md'])

    Returns:
        True if valid, False otherwise
    """
    path = Path(file_path)

    if not path.exists():
        logger.error(f"File does not exist: {file_path}")
        return False

    if allowed_extensions and path.suffix.lower() not in allowed_extensions:
        logger.error(f"File extension not allowed: {path.suffix}. Allowed: {allowed_extensions}")
        return False

    return True


def validate_ticket_content(content: str) -> Dict[str, Any]:
    """
    Validate ticket content for processing.

    Args:
        content: Ticket message content

    Returns:
        Dict with validation results and sanitized content
    """
    if not content or not content.strip():
        return {"valid": False, "error": "Empty content"}

    # Remove excessive whitespace
    sanitized = re.sub(r'\s+', ' ', content.strip())

    # Check minimum length
    if len(sanitized) < 10:
        return {"valid": False, "error": "Content too short"}

    # Check maximum length (reasonable limit)
    if len(sanitized) > 10000:
        return {"valid": False, "error": "Content too long"}

    return {"valid": True, "content": sanitized}


def validate_citations_format(citations: List[Dict[str, Any]]) -> bool:
    """
    Validate citation format in response drafts.

    Args:
        citations: List of citation dictionaries

    Returns:
        True if all citations are properly formatted
    """
    required_fields = ["doc_id", "chunk_id", "title", "score", "url"]

    for citation in citations:
        if not all(field in citation for field in required_fields):
            logger.error(f"Missing required fields in citation: {citation}")
            return False

        # Validate score range
        if not (0.0 <= citation["score"] <= 1.0):
            logger.error(f"Invalid score in citation: {citation['score']}")
            return False

        # Validate URL format (basic check)
        if not citation["url"].startswith(("http://", "https://")):
            logger.error(f"Invalid URL in citation: {citation['url']}")
            return False

    return True


def check_policy_violations(draft: str) -> Dict[str, Any]:
    """
    Check draft response for policy violations.

    Args:
        draft: Generated response draft

    Returns:
        Dict with violation flags and details
    """
    violations = {
        "refund_promise": False,
        "sla_promise": False,
        "escalation_triggers": []
    }

    # Check for refund promises
    refund_patterns = [
        r"we will refund",
        r"refund you",
        r"process your refund",
        r"refund will be issued"
    ]

    for pattern in refund_patterns:
        if re.search(pattern, draft, re.IGNORECASE):
            violations["refund_promise"] = True
            break

    # Check for SLA promises
    sla_patterns = [
        r"within (\d+) hours",
        r"fixed in (\d+) days",
        r"resolved by",
        r"guaranteed"
    ]

    for pattern in sla_patterns:
        if re.search(pattern, draft, re.IGNORECASE):
            violations["sla_promise"] = True
            break

    # Check for escalation triggers
    escalation_keywords = [
        "legal action",
        "lawyer",
        "court",
        "cancel account",
        "close account",
        "delete account"
    ]

    for keyword in escalation_keywords:
        if keyword.lower() in draft.lower():
            violations["escalation_triggers"].append(keyword)

    return violations


def sanitize_input(text: str) -> str:
    """
    Sanitize user input to prevent injection attacks.

    Args:
        text: Input text to sanitize

    Returns:
        Sanitized text
    """
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>]', '', text)

    # Limit length
    if len(sanitized) > 5000:
        sanitized = sanitized[:5000] + "..."

    return sanitized.strip()