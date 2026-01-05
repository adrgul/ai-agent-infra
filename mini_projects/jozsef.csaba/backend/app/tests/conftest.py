"""
Pytest configuration and shared fixtures.

Why this module exists:
- Centralized test fixtures available to all test modules
- Mock settings for testing without real API keys
- TestClient fixture for FastAPI integration tests

Design decisions:
- Override settings with fake values to avoid requiring real API keys in tests
- Use dependency_override to inject mock settings into FastAPI app
- TestClient provides synchronous HTTP client for testing async FastAPI endpoints
"""

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.main import app


def get_mock_settings() -> Settings:
    """
    Create mock settings for testing.

    Why this exists: Tests should not require real API keys or
    access to external services (OpenAI, LangSmith).

    Why fake key format: OpenAI client may validate key format,
    so we use a plausible-looking fake key.

    Returns:
        Settings: Mock settings with fake credentials
    """
    # Assert: Mock settings must be valid (Pydantic will validate)

    return Settings(
        OPENAI_API_KEY="sk-test-fake-key-for-testing-only",
        OPENAI_CHAT_MODEL="gpt-4.1-mini",
        OPENAI_EMBED_MODEL="text-embedding-3-small",
        DOCS_PATH="../data",
        VECTORSTORE_DIR="../.vectorstore/faiss_index_test",
        LANGSMITH_TRACING=False,
        LANGSMITH_API_KEY=None,
        LANGSMITH_PROJECT="test-project",
    )


@pytest.fixture
def mock_settings() -> Settings:
    """
    Pytest fixture providing mock settings.

    Why fixture: Makes mock settings available to any test that needs them
    via pytest's dependency injection.

    Returns:
        Settings: Mock settings instance
    """
    return get_mock_settings()


@pytest.fixture
def client(mock_settings: Settings) -> TestClient:
    """
    Pytest fixture providing TestClient with mocked settings.

    Why this exists: Integration tests need an HTTP client to call API endpoints.
    TestClient allows testing without running an actual server.

    Why dependency override: Injects mock settings into the app so tests
    don't require real environment variables.

    Args:
        mock_settings: Mock settings from fixture

    Returns:
        TestClient: HTTP client for testing FastAPI endpoints
    """
    # Assert: app must be FastAPI instance
    assert app is not None, "FastAPI app must be initialized"

    # Override the settings dependency with mock settings
    # Why: Ensures get_settings() returns mock values during tests
    app.dependency_overrides[get_settings] = lambda: mock_settings

    # Create test client (synchronous HTTP client for async FastAPI app)
    test_client = TestClient(app)

    yield test_client

    # Cleanup: Remove dependency override after test
    # Why: Prevents test pollution (overrides affecting other tests)
    app.dependency_overrides.clear()
