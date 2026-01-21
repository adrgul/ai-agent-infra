"""
Text normalization utilities.
"""
import re


def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace in text.
    
    - Replaces multiple spaces with single space
    - Strips leading/trailing whitespace
    - Normalizes newlines
    
    Args:
        text: Input text
        
    Returns:
        Normalized text
    """
    # Replace multiple whitespace with single space
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def truncate_text(text: str, max_length: int = 1000, suffix: str = "...") -> str:
    """
    Truncate text to maximum length.
    
    Args:
        text: Input text
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def count_tokens_approx(text: str) -> int:
    """
    Approximate token count (simple word-based heuristic).
    
    Real tokenization would use tiktoken or similar.
    This is good enough for demo purposes.
    
    Args:
        text: Input text
        
    Returns:
        Approximate token count
    """
    # Simple approximation: split on whitespace
    # Real tokens are ~1.3x words for English
    words = len(text.split())
    return int(words * 1.3)
