"""
Centralized error handling and retry logic for external API calls.
Handles OpenAI rate limits, timeouts, and server errors with exponential backoff.
"""
import logging
import time
import functools
from typing import Callable, Any, TypeVar, Optional
from openai import (
    APIError,
    APIConnectionError,
    RateLimitError,
    APITimeoutError,
    AuthenticationError,
    PermissionDeniedError,
)

logger = logging.getLogger(__name__)

T = TypeVar('T')


class APICallError(Exception):
    """Custom exception for API call failures after all retries."""
    pass


def estimate_tokens(text: str) -> int:
    """
    Estimate token count (rough approximation).
    Rule of thumb: 1 token ≈ 4 characters for English text.
    
    Args:
        text: Input text
        
    Returns:
        Estimated token count
    """
    return len(text) // 4


def estimate_cost(
    prompt_tokens: int,
    completion_tokens: int,
    model: str = "gpt-4o-mini"
) -> float:
    """
    Estimate API call cost in USD.
    
    Args:
        prompt_tokens: Input token count
        completion_tokens: Output token count
        model: Model name
        
    Returns:
        Estimated cost in USD
    """
    # Prices per 1M tokens (as of Dec 2024)
    prices = {
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-4o": {"input": 2.50, "output": 10.00},
        "gpt-4": {"input": 30.00, "output": 60.00},
        "text-embedding-3-small": {"input": 0.02, "output": 0.0},
        "text-embedding-3-large": {"input": 0.13, "output": 0.0},
    }
    
    if model not in prices:
        logger.warning(f"Unknown model '{model}', using gpt-4o-mini pricing")
        model = "gpt-4o-mini"
    
    price = prices[model]
    cost = (
        (prompt_tokens * price["input"]) + 
        (completion_tokens * price["output"])
    ) / 1_000_000
    
    return cost


def check_token_limit(text: str, max_tokens: int = 120000) -> None:
    """
    Check if text exceeds token limit.
    
    Args:
        text: Input text
        max_tokens: Maximum allowed tokens (default: 120k for gpt-4o-mini)
        
    Raises:
        ValueError: If text exceeds token limit
    """
    estimated = estimate_tokens(text)
    if estimated > max_tokens:
        raise ValueError(
            f"Text too long: {estimated} tokens (max: {max_tokens}). "
            f"Please reduce context or chunk the request."
        )


def retry_with_exponential_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
) -> Callable:
    """
    Decorator for retrying API calls with exponential backoff.
    
    Handles:
    - RateLimitError (429): Retry with exponential backoff
    - APIConnectionError: Network issues, retry
    - APITimeoutError: Timeout, retry with longer wait
    - APIError (500+): Server errors, retry
    - AuthenticationError (401): Don't retry, raise immediately
    - PermissionDeniedError (403): Don't retry, raise immediately
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        exponential_base: Base for exponential backoff
        jitter: Add random jitter to prevent thundering herd
        
    Usage:
        @retry_with_exponential_backoff(max_retries=3)
        def call_openai_api():
            return client.chat.completions.create(...)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            delay = initial_delay
            
            for attempt in range(max_retries):
                try:
                    result = func(*args, **kwargs)
                    
                    # Log successful call after retries
                    if attempt > 0:
                        logger.info(f"{func.__name__} succeeded after {attempt + 1} attempts")
                    
                    return result
                    
                except RateLimitError as e:
                    # Rate limit hit (429)
                    if attempt == max_retries - 1:
                        logger.error(f"Rate limit exceeded after {max_retries} attempts")
                        raise APICallError(f"Rate limit exceeded: {e}") from e
                    
                    # Check for Retry-After header
                    retry_after = getattr(e, 'retry_after', None)
                    if retry_after:
                        wait_time = float(retry_after)
                    else:
                        wait_time = delay * (exponential_base ** attempt)
                        if jitter:
                            import random
                            wait_time *= (0.5 + random.random())  # 50-150% of base delay
                    
                    logger.warning(
                        f"{func.__name__} rate limited (attempt {attempt + 1}/{max_retries}). "
                        f"Waiting {wait_time:.1f}s..."
                    )
                    time.sleep(wait_time)
                    
                except APITimeoutError as e:
                    # Timeout error
                    if attempt == max_retries - 1:
                        logger.error(f"Timeout after {max_retries} attempts")
                        raise APICallError(f"Request timeout: {e}") from e
                    
                    wait_time = delay * (exponential_base ** attempt)
                    logger.warning(
                        f"{func.__name__} timed out (attempt {attempt + 1}/{max_retries}). "
                        f"Waiting {wait_time:.1f}s..."
                    )
                    time.sleep(wait_time)
                    
                except APIConnectionError as e:
                    # Network/connection error
                    if attempt == max_retries - 1:
                        logger.error(f"Connection failed after {max_retries} attempts")
                        raise APICallError(f"Connection error: {e}") from e
                    
                    wait_time = delay * (exponential_base ** attempt)
                    logger.warning(
                        f"{func.__name__} connection failed (attempt {attempt + 1}/{max_retries}). "
                        f"Waiting {wait_time:.1f}s..."
                    )
                    time.sleep(wait_time)
                    
                except APIError as e:
                    # Generic API error (likely 500+ server error)
                    if attempt == max_retries - 1:
                        logger.error(f"API error after {max_retries} attempts: {e}")
                        raise APICallError(f"API error: {e}") from e
                    
                    # Check if it's a server error (5xx) - retry
                    # Client errors (4xx except 429) - don't retry
                    status_code = getattr(e, 'status_code', None)
                    if status_code and 400 <= status_code < 500:
                        # Client error, don't retry
                        logger.error(f"Client error {status_code}: {e}")
                        raise APICallError(f"Client error {status_code}: {e}") from e
                    
                    wait_time = delay * (exponential_base ** attempt)
                    logger.warning(
                        f"{func.__name__} API error (attempt {attempt + 1}/{max_retries}). "
                        f"Waiting {wait_time:.1f}s..."
                    )
                    time.sleep(wait_time)
                    
                except AuthenticationError as e:
                    # Authentication failed (401) - don't retry
                    logger.error(f"Authentication failed: {e}")
                    raise APICallError(f"Authentication error: {e}") from e
                    
                except PermissionDeniedError as e:
                    # Permission denied (403) - don't retry
                    logger.error(f"Permission denied: {e}")
                    raise APICallError(f"Permission denied: {e}") from e
                    
            # Should never reach here, but just in case
            raise APICallError(f"Max retries ({max_retries}) exceeded")
        
        return wrapper
    return decorator


class TokenUsageTracker:
    """Track token usage and costs across API calls."""
    
    def __init__(self):
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_cost = 0.0
        self.call_count = 0
        
    def track(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        model: str = "gpt-4o-mini"
    ) -> None:
        """
        Record token usage from an API call.
        
        Args:
            prompt_tokens: Input tokens
            completion_tokens: Output tokens
            model: Model used
        """
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        cost = estimate_cost(prompt_tokens, completion_tokens, model)
        self.total_cost += cost
        self.call_count += 1
        
        logger.info(
            f"API call #{self.call_count}: {prompt_tokens} + {completion_tokens} tokens, "
            f"cost: ${cost:.6f} (total: ${self.total_cost:.4f})"
        )
        
    def get_summary(self) -> dict:
        """Get usage summary."""
        return {
            "calls": self.call_count,
            "prompt_tokens": self.total_prompt_tokens,
            "completion_tokens": self.total_completion_tokens,
            "total_tokens": self.total_prompt_tokens + self.total_completion_tokens,
            "total_cost_usd": round(self.total_cost, 4),
        }
        
    def reset(self) -> None:
        """Reset tracker."""
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_cost = 0.0
        self.call_count = 0


# Global tracker instance
usage_tracker = TokenUsageTracker()
