"""
Contract tests for /chat endpoint.

Why this module exists:
- Validates chat response schema and structure
- Tests chat with fake LLM and fake embeddings (no OpenAI calls)
- Verifies source attribution format

Design decisions:
- Create temp vector store with fake embeddings
- Inject fake LLM to avoid OpenAI API calls
- Verify response structure matches Pydantic schema
"""

import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.main import app
from app.rag.chain import create_chat_llm
from app.rag.embeddings import create_embeddings
from app.tests.test_fakes import FakeEmbeddings, FakeLLM


def test_chat_contract_with_fake_llm():
    """
    Test /chat endpoint contract with fake LLM and embeddings.

    Why this test: Validates that chat response has correct structure:
    - answer is non-empty string
    - sources is list of SourceAttribution objects
    - model field matches config
    - session_id is echoed back

    Why fake LLM/embeddings: Avoids OpenAI API calls during testing.
    Tests contract regardless of actual LLM response content.
    """
    # Assert: Response must match ChatResponse schema

    with tempfile.TemporaryDirectory() as temp_docs_dir, \
         tempfile.TemporaryDirectory() as temp_vs_dir:

        # Create test markdown file
        test_file = Path(temp_docs_dir) / "test.md"
        test_file.write_text("# Test Document\n\nThis is a test document for contract testing.")

        test_settings = Settings(
            OPENAI_API_KEY="sk-test-fake-key",
            OPENAI_CHAT_MODEL="gpt-4.1-mini",
            OPENAI_EMBED_MODEL="text-embedding-3-small",
            DOCS_PATH=temp_docs_dir,
            VECTORSTORE_DIR=temp_vs_dir,
            LANGSMITH_TRACING=False,
        )

        # Override create_embeddings and create_chat_llm to return fakes
        fake_embeddings = FakeEmbeddings()
        fake_llm = FakeLLM(response="This is a fake answer from the fake LLM.")

        import app.rag.embeddings
        import app.rag.chain

        original_create_embeddings = app.rag.embeddings.create_embeddings
        original_create_chat_llm = app.rag.chain.create_chat_llm

        app.rag.embeddings.create_embeddings = lambda settings: fake_embeddings
        app.rag.chain.create_chat_llm = lambda settings: fake_llm

        app.dependency_overrides[get_settings] = lambda: test_settings

        try:
            client = TestClient(app)

            # First, call /ingest to create vector store
            ingest_response = client.post("/ingest", json={"force_rebuild": True})
            assert ingest_response.status_code == 200, (
                f"Ingest failed: {ingest_response.text}"
            )

            # Now call /chat
            chat_response = client.post(
                "/chat",
                json={
                    "session_id": "test-session-123",
                    "message": "What is this document about?",
                    "top_k": 2,
                    "temperature": 0.2,
                }
            )

            # Verify status code
            assert chat_response.status_code == 200, (
                f"Chat must return 200, got {chat_response.status_code}: {chat_response.text}"
            )

            # Verify response structure
            data = chat_response.json()

            # Check required fields
            assert "session_id" in data, "Response must contain session_id"
            assert "answer" in data, "Response must contain answer"
            assert "sources" in data, "Response must contain sources"
            assert "model" in data, "Response must contain model"

            # Verify session_id echoed
            assert data["session_id"] == "test-session-123", (
                "session_id must be echoed back"
            )

            # Verify answer is non-empty string
            assert isinstance(data["answer"], str), "answer must be string"
            assert len(data["answer"]) > 0, "answer must not be empty"

            # Verify sources structure
            assert isinstance(data["sources"], list), "sources must be list"
            assert len(data["sources"]) > 0, "sources must not be empty"

            # Check first source has required fields
            source = data["sources"][0]
            assert "source_id" in source, "Source must have source_id"
            assert "filename" in source, "Source must have filename"
            assert "snippet" in source, "Source must have snippet"

            # Verify model matches config
            assert data["model"] == "gpt-4.1-mini", (
                f"Model must match config, got {data['model']}"
            )

        finally:
            # Restore original functions
            app.rag.embeddings.create_embeddings = original_create_embeddings
            app.rag.chain.create_chat_llm = original_create_chat_llm
            app.dependency_overrides.clear()


def test_chat_validates_request():
    """
    Test that /chat validates request parameters.

    Why this test: Ensures Pydantic validation works for:
    - Empty message
    - Invalid top_k range
    - Invalid temperature range
    """
    # Assert: Invalid requests must return 422

    with tempfile.TemporaryDirectory() as temp_docs_dir, \
         tempfile.TemporaryDirectory() as temp_vs_dir:

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

            # Test empty message (min_length=1)
            response = client.post(
                "/chat",
                json={
                    "message": "",
                    "top_k": 4,
                }
            )
            assert response.status_code == 422, "Empty message must return 422"

            # Test invalid top_k (below minimum)
            response = client.post(
                "/chat",
                json={
                    "message": "test",
                    "top_k": 0,
                }
            )
            assert response.status_code == 422, "top_k=0 must return 422"

            # Test invalid top_k (above maximum)
            response = client.post(
                "/chat",
                json={
                    "message": "test",
                    "top_k": 21,
                }
            )
            assert response.status_code == 422, "top_k=21 must return 422"

            # Test invalid temperature (below minimum)
            response = client.post(
                "/chat",
                json={
                    "message": "test",
                    "temperature": -0.1,
                }
            )
            assert response.status_code == 422, "temperature=-0.1 must return 422"

            # Test invalid temperature (above maximum)
            response = client.post(
                "/chat",
                json={
                    "message": "test",
                    "temperature": 1.1,
                }
            )
            assert response.status_code == 422, "temperature=1.1 must return 422"

        finally:
            app.dependency_overrides.clear()
