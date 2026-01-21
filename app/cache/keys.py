"""
Cache key normalization utilities.
Ensures consistent cache keys across the application.
"""
import hashlib
import json
from typing import Any


def normalize_text(text: str) -> str:
    """
    Normalize text for cache key generation.
    
    - Lowercase
    - Strip whitespace
    - Remove extra spaces
    
    Args:
        text: Input text
        
    Returns:
        Normalized text
    """
    return " ".join(text.lower().strip().split())


def generate_cache_key(prefix: str, *args: Any, **kwargs: Any) -> str:
    """
    Generate a deterministic cache key.
    
    Args:
        prefix: Key prefix (e.g., node name)
        *args: Positional arguments to include in key
        **kwargs: Keyword arguments to include in key
        
    Returns:
        Hashed cache key
    """
    # Normalize text arguments
    normalized_args = []
    for arg in args:
        if isinstance(arg, str):
            normalized_args.append(normalize_text(arg))
        else:
            normalized_args.append(arg)
    
    # Create deterministic representation
    key_data = {
        "prefix": prefix,
        "args": normalized_args,
        "kwargs": sorted(kwargs.items())
    }
    
    # Hash for consistent length
    key_json = json.dumps(key_data, sort_keys=True)
    key_hash = hashlib.sha256(key_json.encode()).hexdigest()
    
    return f"{prefix}:{key_hash}"
