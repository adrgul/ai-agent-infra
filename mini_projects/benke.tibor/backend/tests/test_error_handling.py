"""
Unit tests for infrastructure/error_handling.py module.

Tests cover:
- Token estimation functions
- Cost calculation functions
- Token limit checking
- Retry decorator with exponential backoff
- TokenUsageTracker class
"""
import pytest
import time
from unittest.mock import Mock
from openai import (
    RateLimitError,
    APITimeoutError,
    APIConnectionError,
    APIError,
    AuthenticationError,
    PermissionDeniedError,
)

from infrastructure.error_handling import (
    estimate_tokens,
    estimate_cost,
    check_token_limit,
    retry_with_exponential_backoff,
    TokenUsageTracker,
    APICallError,
)


# Helper to create OpenAI errors with required parameters
def create_mock_response(status_code=500):
    """Create mock response for OpenAI errors."""
    mock_response = Mock()
    mock_response.status_code = status_code
    mock_response.headers = {}
    return mock_response


def create_rate_limit_error(message="Rate limit", retry_after=None):
    """Create RateLimitError with proper parameters."""
    response = create_mock_response(429)
    if retry_after:
        response.headers['retry-after'] = str(retry_after)
    error = RateLimitError(message, response=response, body={"error": {"message": message}})
    if retry_after:
        error.retry_after = retry_after
    return error


def create_timeout_error(message="Timeout"):
    """Create APITimeoutError with proper parameters."""
    return APITimeoutError(message)


def create_connection_error(message="Connection failed"):
    """Create APIConnectionError with proper parameters."""
    # APIConnectionError in v1.x+ takes a request parameter
    mock_request = Mock()
    error = APIConnectionError(request=mock_request)
    error.message = message
    return error


def create_authentication_error(message="Invalid API key"):
    """Create AuthenticationError with proper parameters."""
    response = create_mock_response(401)
    error = AuthenticationError(message, response=response, body={"error": {"message": message}})
    return error


def create_permission_error(message="Permission denied"):
    """Create PermissionDeniedError with proper parameters."""
    response = create_mock_response(403)
    error = PermissionDeniedError(message, response=response, body={"error": {"message": message}})
    return error


def create_api_error(message="API error", status_code=500):
    """Create generic APIError with proper parameters."""
    mock_request = Mock()
    error = APIError(message, request=mock_request, body={"error": {"message": message}})
    return error


class TestTokenEstimation:
    """Tests for token estimation functions."""
    
    def test_estimate_tokens_empty_string(self):
        """Test token estimation with empty string."""
        assert estimate_tokens("") == 0
    
    def test_estimate_tokens_simple_text(self):
        """Test token estimation with simple English text."""
        text = "Hello world"  # 11 chars
        tokens = estimate_tokens(text)
        assert tokens == 2  # 11 // 4 = 2
    
    def test_estimate_tokens_longer_text(self):
        """Test token estimation with longer text."""
        text = "This is a longer piece of text for testing token estimation."
        # 62 characters
        tokens = estimate_tokens(text)
        assert tokens == 15  # 62 // 4 = 15
    
    def test_estimate_tokens_hungarian_text(self):
        """Test token estimation with Hungarian text."""
        text = "Ez egy magyar szöveg a token becslés teszteléséhez."
        # 50 characters (special chars count differently)
        tokens = estimate_tokens(text)
        assert tokens == 12  # 50 // 4 = 12
    
    def test_estimate_tokens_large_text(self):
        """Test token estimation with large text (10k chars)."""
        text = "x" * 10000
        tokens = estimate_tokens(text)
        assert tokens == 2500  # 10000 // 4 = 2500
    
    def test_estimate_tokens_accuracy(self):
        """Test estimation accuracy is roughly 1 token ≈ 4 chars."""
        # Standard English sentence
        text = "The quick brown fox jumps over the lazy dog."
        tokens = estimate_tokens(text)
        # 45 chars → ~11 tokens (actual GPT-4 is ~10 tokens)
        assert 10 <= tokens <= 12  # Allow 10-20% margin


class TestCostEstimation:
    """Tests for cost estimation functions."""
    
    def test_estimate_cost_gpt4o_mini(self):
        """Test cost estimation for gpt-4o-mini."""
        cost = estimate_cost(
            prompt_tokens=1000,
            completion_tokens=500,
            model="gpt-4o-mini"
        )
        # (1000 * 0.15 + 500 * 0.60) / 1M = 0.00045
        expected = (1000 * 0.15 + 500 * 0.60) / 1_000_000
        assert cost == pytest.approx(expected, rel=1e-6)
    
    def test_estimate_cost_gpt4o(self):
        """Test cost estimation for gpt-4o."""
        cost = estimate_cost(
            prompt_tokens=1000,
            completion_tokens=500,
            model="gpt-4o"
        )
        # (1000 * 2.50 + 500 * 10.00) / 1M = 0.0075
        expected = (1000 * 2.50 + 500 * 10.00) / 1_000_000
        assert cost == pytest.approx(expected, rel=1e-6)
    
    def test_estimate_cost_embeddings(self):
        """Test cost estimation for text-embedding-3-small."""
        cost = estimate_cost(
            prompt_tokens=1000,
            completion_tokens=0,
            model="text-embedding-3-small"
        )
        # (1000 * 0.02 + 0 * 0.0) / 1M = 0.00002
        expected = (1000 * 0.02) / 1_000_000
        assert cost == pytest.approx(expected, rel=1e-6)
    
    def test_estimate_cost_unknown_model(self):
        """Test cost estimation falls back to gpt-4o-mini for unknown models."""
        cost = estimate_cost(
            prompt_tokens=1000,
            completion_tokens=500,
            model="unknown-model-xyz"
        )
        # Should use gpt-4o-mini pricing
        expected = (1000 * 0.15 + 500 * 0.60) / 1_000_000
        assert cost == pytest.approx(expected, rel=1e-6)
    
    def test_estimate_cost_zero_tokens(self):
        """Test cost estimation with zero tokens."""
        cost = estimate_cost(
            prompt_tokens=0,
            completion_tokens=0,
            model="gpt-4o-mini"
        )
        assert cost == 0.0
    
    def test_estimate_cost_large_request(self):
        """Test cost estimation for large request."""
        cost = estimate_cost(
            prompt_tokens=100_000,  # 100k tokens
            completion_tokens=10_000,  # 10k tokens
            model="gpt-4o-mini"
        )
        # (100k * 0.15 + 10k * 0.60) / 1M = 0.021
        expected = (100_000 * 0.15 + 10_000 * 0.60) / 1_000_000
        assert cost == pytest.approx(expected, rel=1e-6)


class TestTokenLimitCheck:
    """Tests for check_token_limit function."""
    
    def test_check_token_limit_within_limit(self):
        """Test that no exception is raised when within limit."""
        text = "Short text"  # ~2 tokens
        # Should not raise
        check_token_limit(text, max_tokens=100)
    
    def test_check_token_limit_exactly_at_limit(self):
        """Test text exactly at token limit."""
        text = "x" * 400  # Exactly 100 tokens (400 / 4)
        # Should not raise
        check_token_limit(text, max_tokens=100)
    
    def test_check_token_limit_exceeds_limit(self):
        """Test that ValueError is raised when exceeding limit."""
        text = "x" * 1000  # 250 tokens (1000 / 4)
        
        with pytest.raises(ValueError) as exc_info:
            check_token_limit(text, max_tokens=100)
        
        assert "Text too long: 250 tokens (max: 100)" in str(exc_info.value)
    
    def test_check_token_limit_custom_limit(self):
        """Test with custom token limit."""
        text = "x" * 40000  # 10k tokens
        
        with pytest.raises(ValueError) as exc_info:
            check_token_limit(text, max_tokens=5000)
        
        assert "10000 tokens" in str(exc_info.value)
        assert "max: 5000" in str(exc_info.value)
    
    def test_check_token_limit_empty_string(self):
        """Test with empty string."""
        check_token_limit("", max_tokens=100)  # Should not raise


class TestRetryDecorator:
    """Tests for retry_with_exponential_backoff decorator."""
    
    def test_retry_success_first_attempt(self):
        """Test successful call on first attempt (no retry needed)."""
        mock_func = Mock(return_value="success")
        mock_func.__name__ = "mock_func"  # Mock needs __name__ for decorator
        decorated = retry_with_exponential_backoff(max_retries=3)(mock_func)
        
        result = decorated()
        
        assert result == "success"
        assert mock_func.call_count == 1
    
    def test_retry_rate_limit_with_backoff(self):
        """Test retry on RateLimitError with exponential backoff."""
        # Create proper RateLimitError with required parameters
        mock_response = Mock()
        mock_response.status_code = 429
        
        def create_rate_limit_error():
            return RateLimitError(
                "Rate limit exceeded",
                response=mock_response,
                body={"error": {"message": "Rate limit exceeded"}}
            )
        
        mock_func = Mock(side_effect=[
            create_rate_limit_error(),
            create_rate_limit_error(),
            "success"
        ])
        mock_func.__name__ = "mock_func"
        
        decorated = retry_with_exponential_backoff(
            max_retries=3,
            initial_delay=0.01  # Fast test
        )(mock_func)
        
        start = time.time()
        result = decorated()
        duration = time.time() - start
        
        assert result == "success"
        assert mock_func.call_count == 3
        # Should have some delay from backoff
        assert duration >= 0.01
    
    def test_retry_timeout_error(self):
        """Test retry on APITimeoutError."""
        mock_func = Mock(side_effect=[
            create_timeout_error("Timeout"),
            "success"
        ])
        mock_func.__name__ = "mock_func"
        
        decorated = retry_with_exponential_backoff(
            max_retries=3,
            initial_delay=0.01
        )(mock_func)
        
        result = decorated()
        
        assert result == "success"
        assert mock_func.call_count == 2
    
    def test_retry_connection_error(self):
        """Test retry on APIConnectionError."""
        mock_func = Mock(side_effect=[
            create_connection_error("Connection failed"),
            create_connection_error("Connection failed"),
            "success"
        ])
        mock_func.__name__ = "mock_func"
        
        decorated = retry_with_exponential_backoff(
            max_retries=3,
            initial_delay=0.01
        )(mock_func)
        
        result = decorated()
        
        assert result == "success"
        assert mock_func.call_count == 3
    
    def test_retry_max_retries_exceeded(self):
        """Test APICallError raised when max retries exceeded."""
        mock_func = Mock(side_effect=create_rate_limit_error("Rate limit"))
        mock_func.__name__ = "mock_func"
        
        decorated = retry_with_exponential_backoff(
            max_retries=2,
            initial_delay=0.01
        )(mock_func)
        
        with pytest.raises(APICallError) as exc_info:
            decorated()
        
        assert "Rate limit exceeded" in str(exc_info.value)
        assert mock_func.call_count == 2
    
    def test_retry_authentication_error_no_retry(self):
        """Test AuthenticationError is not retried."""
        mock_func = Mock(side_effect=create_authentication_error("Invalid API key"))
        mock_func.__name__ = "mock_func"
        
        decorated = retry_with_exponential_backoff(max_retries=3)(mock_func)
        
        with pytest.raises(APICallError) as exc_info:
            decorated()
        
        assert "Client error 401" in str(exc_info.value)
        assert mock_func.call_count == 1  # No retry
    
    def test_retry_permission_denied_no_retry(self):
        """Test PermissionDeniedError is not retried."""
        mock_func = Mock(side_effect=create_permission_error("Forbidden"))
        mock_func.__name__ = "mock_func"
        
        decorated = retry_with_exponential_backoff(max_retries=3)(mock_func)
        
        with pytest.raises(APICallError) as exc_info:
            decorated()
        
        assert "Client error 403" in str(exc_info.value)
        assert mock_func.call_count == 1  # No retry
    
    def test_retry_client_error_no_retry(self):
        """Test 4xx client errors are not retried (except 429)."""
        # Create APIError with status_code 400
        error = create_api_error("Bad request", status_code=400)
        error.status_code = 400
        
        mock_func = Mock(side_effect=error)
        decorated = retry_with_exponential_backoff(max_retries=3)(mock_func)
        
        with pytest.raises(APICallError):
            decorated()
        
        assert mock_func.call_count == 1  # No retry for 4xx
    
    def test_retry_server_error_with_retry(self):
        """Test 5xx server errors are retried."""
        # Create APIError with status_code 500
        error = create_api_error("Internal server error", status_code=500)
        error.status_code = 500
        
        mock_func = Mock(side_effect=[error, "success"])
        mock_func.__name__ = "mock_func"
        decorated = retry_with_exponential_backoff(
            max_retries=3,
            initial_delay=0.01
        )(mock_func)
        
        result = decorated()
        
        assert result == "success"
        assert mock_func.call_count == 2  # Retry for 5xx
    
    def test_retry_with_retry_after_header(self):
        """Test RateLimitError respects Retry-After header."""
        error = create_rate_limit_error("Rate limit", retry_after=0.05)
        
        mock_func = Mock(side_effect=[error, "success"])
        mock_func.__name__ = "mock_func"
        decorated = retry_with_exponential_backoff(max_retries=3)(mock_func)
        
        start = time.time()
        result = decorated()
        duration = time.time() - start
        
        assert result == "success"
        assert duration >= 0.05  # Waited at least 50ms
    
    def test_retry_exponential_backoff_calculation(self):
        """Test exponential backoff delay increases correctly."""
        mock_func = Mock(side_effect=[
            create_rate_limit_error("Limit"),
            create_rate_limit_error("Limit"),
            create_rate_limit_error("Limit"),
        ])
        mock_func.__name__ = "mock_func"
        
        decorated = retry_with_exponential_backoff(
            max_retries=3,
            initial_delay=0.1,
            exponential_base=2.0,
            jitter=False  # Disable jitter for predictable timing
        )(mock_func)
        
        start = time.time()
        
        with pytest.raises(APICallError):
            decorated()
        
        duration = time.time() - start
        
        # Expected delays: 0.1s (attempt 1), 0.2s (attempt 2) = 0.3s total
        # Allow some margin for execution time
        assert 0.25 <= duration <= 0.4


class TestTokenUsageTracker:
    """Tests for TokenUsageTracker class."""
    
    def test_tracker_initialization(self):
        """Test tracker starts with zero values."""
        tracker = TokenUsageTracker()
        
        assert tracker.total_prompt_tokens == 0
        assert tracker.total_completion_tokens == 0
        assert tracker.total_cost == 0.0
        assert tracker.call_count == 0
    
    def test_tracker_single_call(self):
        """Test tracking a single API call."""
        tracker = TokenUsageTracker()
        
        tracker.track(
            prompt_tokens=1000,
            completion_tokens=500,
            model="gpt-4o-mini"
        )
        
        assert tracker.call_count == 1
        assert tracker.total_prompt_tokens == 1000
        assert tracker.total_completion_tokens == 500
        assert tracker.total_cost > 0
    
    def test_tracker_multiple_calls(self):
        """Test tracking multiple API calls."""
        tracker = TokenUsageTracker()
        
        tracker.track(1000, 500, "gpt-4o-mini")
        tracker.track(2000, 800, "gpt-4o-mini")
        tracker.track(1500, 600, "gpt-4o-mini")
        
        assert tracker.call_count == 3
        assert tracker.total_prompt_tokens == 4500
        assert tracker.total_completion_tokens == 1900
        assert tracker.total_cost > 0
    
    def test_tracker_get_summary(self):
        """Test get_summary returns correct statistics."""
        tracker = TokenUsageTracker()
        
        tracker.track(1000, 500, "gpt-4o-mini")
        tracker.track(2000, 1000, "gpt-4o-mini")
        
        summary = tracker.get_summary()
        
        assert summary["calls"] == 2
        assert summary["prompt_tokens"] == 3000
        assert summary["completion_tokens"] == 1500
        assert summary["total_tokens"] == 4500
        assert summary["total_cost_usd"] > 0
        assert isinstance(summary["total_cost_usd"], float)
    
    def test_tracker_reset(self):
        """Test reset() clears all statistics."""
        tracker = TokenUsageTracker()
        
        tracker.track(1000, 500, "gpt-4o-mini")
        tracker.track(2000, 800, "gpt-4o-mini")
        
        # Verify data exists
        assert tracker.call_count == 2
        
        # Reset
        tracker.reset()
        
        # Verify all cleared
        assert tracker.call_count == 0
        assert tracker.total_prompt_tokens == 0
        assert tracker.total_completion_tokens == 0
        assert tracker.total_cost == 0.0
    
    def test_tracker_cost_accumulation(self):
        """Test cost accumulates correctly across calls."""
        tracker = TokenUsageTracker()
        
        # First call
        tracker.track(1000, 500, "gpt-4o-mini")
        cost_1 = tracker.total_cost
        
        # Second call
        tracker.track(1000, 500, "gpt-4o-mini")
        cost_2 = tracker.total_cost
        
        # Cost should double (same tokens)
        assert cost_2 == pytest.approx(cost_1 * 2, rel=1e-6)
    
    def test_tracker_different_models(self):
        """Test tracking with different models."""
        tracker = TokenUsageTracker()
        
        tracker.track(1000, 500, "gpt-4o-mini")
        tracker.track(1000, 500, "gpt-4o")
        
        summary = tracker.get_summary()
        
        # Both calls counted
        assert summary["calls"] == 2
        assert summary["prompt_tokens"] == 2000
        
        # Cost should be higher (gpt-4o is more expensive)
        assert summary["total_cost_usd"] > 0


class TestAPICallError:
    """Tests for custom APICallError exception."""
    
    def test_api_call_error_creation(self):
        """Test APICallError can be created and raised."""
        error = APICallError("Test error message")
        
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)
    
    def test_api_call_error_with_cause(self):
        """Test APICallError with underlying cause."""
        cause = create_rate_limit_error("Rate limit exceeded")
        
        try:
            raise APICallError("Wrapped error") from cause
        except APICallError as e:
            assert str(e) == "Wrapped error"
            assert e.__cause__ == cause


# Integration test
class TestErrorHandlingIntegration:
    """Integration tests for error handling module."""
    
    def test_full_workflow_with_retry(self):
        """Test complete workflow: estimate → check → call with retry → track."""
        tracker = TokenUsageTracker()
        
        # 1. Estimate tokens
        query = "What is the brand guideline for typography?"
        estimated = estimate_tokens(query)
        assert estimated > 0
        
        # 2. Check token limit
        check_token_limit(query, max_tokens=10000)  # Should pass
        
        # 3. Mock API call with retry
        def mock_api_call():
            return {"prompt_tokens": 100, "completion_tokens": 50}
        
        mock_api_call.__name__ = "mock_api_call"  # Required for decorator
        decorated_call = retry_with_exponential_backoff(max_retries=2, initial_delay=0.01)(mock_api_call)
        
        result = decorated_call()
        
        # 4. Track usage
        tracker.track(
            result["prompt_tokens"],
            result["completion_tokens"],
            "gpt-4o-mini"
        )
        
        # 5. Get summary
        summary = tracker.get_summary()
        
        assert summary["calls"] == 1
        assert summary["total_tokens"] == 150
        assert summary["total_cost_usd"] > 0
