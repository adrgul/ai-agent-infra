"""
Test that /chat requires /ingest to be called first.

Why this module exists:
- Validates 409 response when vector store doesn't exist
- Ensures proper error message directing user to call /ingest
- Verifies fail-fast behavior before attempting RAG

Design decisions:
- Test uses clean environment (no vector store)
- Validates status code and error message
"""

import tempfile

from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.main import app


def test_chat_returns_409_when_vectorstore_missing():
    """
    Test that POST /chat returns 409 when vector store doesn't exist.

    Why this test: Verifies that the chat endpoint correctly detects missing
    vector store and returns 409 Conflict with helpful error message.

    Why 409: Conflict status code indicates the resource (vector store)
    must exist before this operation can proceed. Directs user to /ingest.
    """
    # Assert: Response must be 409 when vector store doesn't exist

    with tempfile.TemporaryDirectory() as temp_docs_dir, \
         tempfile.TemporaryDirectory() as temp_vs_dir:

        # temp_vs_dir is empty (no vector store)

        test_settings = Settings(
            OPENAI_API_KEY="sk-test-fake-key",
            OPENAI_CHAT_MODEL="gpt-4.1-mini",
            OPENAI_EMBED_MODEL="text-embedding-3-small",
            DOCS_PATH=temp_docs_dir,
            VECTORSTORE_DIR=temp_vs_dir,
            LANGSMITH_TRACING=False,
        )

        app.dependency_overrides[get_settings] = lambda: test_settings

        try:
            client = TestClient(app)

            # Attempt to chat without calling /ingest first
            response = client.post(
                "/chat",
                json={
                    "message": "What is the answer?",
                    "top_k": 4,
                    "temperature": 0.2,
                }
            )

            # Must return 409 Conflict
            assert response.status_code == 409, (
                f"Expected 409 when vector store missing, got {response.status_code}"
            )

            # Error message should mention vector store and /ingest
            response_text = response.text.lower()
            assert "vector store" in response_text or "index" in response_text, (
                "Error message should mention vector store or index"
            )
            assert "ingest" in response_text, (
                "Error message should direct user to call /ingest"
            )

        finally:
            app.dependency_overrides.clear()
