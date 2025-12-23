"""
Smoke tests for /ingest endpoint.

Why this module exists:
- End-to-end test of ingestion pipeline
- Verifies markdown loading, chunking, and FAISS indexing
- Uses fake embeddings to avoid OpenAI API calls

Design decisions:
- Create temp directory with test markdown files
- Use FakeEmbeddings for deterministic, network-free testing
- Verify vector store files are created
"""

import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import app
from app.rag.embeddings import create_embeddings
from app.tests.test_fakes import FakeEmbeddings


def get_test_settings_with_temp_dirs(temp_docs_dir: str, temp_vs_dir: str) -> Settings:
    """
    Create test settings with temporary directories.

    Args:
        temp_docs_dir: Temporary directory for test markdown files
        temp_vs_dir: Temporary directory for test vector store

    Returns:
        Settings: Test settings instance
    """
    return Settings(
        OPENAI_API_KEY="sk-test-fake-key",
        OPENAI_CHAT_MODEL="gpt-4.1-mini",
        OPENAI_EMBED_MODEL="text-embedding-3-small",
        DOCS_PATH=temp_docs_dir,
        VECTORSTORE_DIR=temp_vs_dir,
        LANGSMITH_TRACING=False,
    )


def test_ingest_smoke():
    """
    Smoke test for POST /ingest endpoint.

    Why this test: Verifies entire ingestion pipeline works end-to-end:
    1. Creates test markdown files
    2. Calls /ingest endpoint
    3. Verifies vector store is created
    4. Checks response contains expected statistics

    Why temp directories: Isolated test environment that cleans up automatically.

    Why fake embeddings: Avoids OpenAI API calls (no cost, no network).
    """
    # Assert: Test must use fake embeddings (verified by no API key errors)

    with tempfile.TemporaryDirectory() as temp_docs_dir, \
         tempfile.TemporaryDirectory() as temp_vs_dir:

        # Create test markdown files
        # Why multiple files: Tests handling of multiple documents
        test_files = {
            "doc1.md": "# Document 1\n\nThis is the first test document with some content.",
            "doc2.md": "# Document 2\n\nThis is the second test document with different content.",
            "subdir/doc3.md": "# Document 3\n\nThis is a document in a subdirectory.",
        }

        for filepath, content in test_files.items():
            full_path = Path(temp_docs_dir) / filepath
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)

        # Override settings with temp directories
        test_settings = get_test_settings_with_temp_dirs(temp_docs_dir, temp_vs_dir)

        # Override create_embeddings to return FakeEmbeddings
        # Why: Inject fake embeddings without modifying production code
        original_create_embeddings = create_embeddings

        def fake_create_embeddings(settings: Settings):
            return FakeEmbeddings()

        # Monkey patch for this test
        import app.rag.embeddings
        app.rag.embeddings.create_embeddings = fake_create_embeddings

        # Override settings dependency
        from app.core.config import get_settings
        app.dependency_overrides[get_settings] = lambda: test_settings

        try:
            # Create test client
            client = TestClient(app)

            # Call /ingest endpoint
            response = client.post("/ingest", json={"force_rebuild": True})

            # Verify response
            assert response.status_code == 200, (
                f"Ingest must return 200, got {response.status_code}: {response.text}"
            )

            data = response.json()

            # Verify response structure
            assert "indexed_files" in data, "Response must contain indexed_files"
            assert "chunk_count" in data, "Response must contain chunk_count"
            assert "vectorstore_dir" in data, "Response must contain vectorstore_dir"
            assert "filenames" in data, "Response must contain filenames"

            # Verify counts
            assert data["indexed_files"] == 3, f"Expected 3 files, got {data['indexed_files']}"
            assert data["chunk_count"] > 0, "Must have at least one chunk"

            # Verify filenames
            assert len(data["filenames"]) == 3, "Must list all 3 filenames"

            # Verify vector store files exist
            vs_dir = Path(temp_vs_dir)
            assert vs_dir.exists(), "Vector store directory must exist"
            assert (vs_dir / "index.faiss").exists(), "index.faiss must exist"
            assert (vs_dir / "index.pkl").exists(), "index.pkl must exist"

        finally:
            # Restore original functions
            app.rag.embeddings.create_embeddings = original_create_embeddings
            app.dependency_overrides.clear()


def test_ingest_no_markdown_files_returns_400():
    """
    Test that /ingest returns 400 when no markdown files found.

    Why this test: Verifies proper error handling when DOCS_PATH is empty
    or contains no .md files.
    """
    # Assert: Response must be 400 when no markdown files found

    with tempfile.TemporaryDirectory() as temp_docs_dir, \
         tempfile.TemporaryDirectory() as temp_vs_dir:

        # Empty directory (no markdown files)

        test_settings = get_test_settings_with_temp_dirs(temp_docs_dir, temp_vs_dir)

        from app.core.config import get_settings
        app.dependency_overrides[get_settings] = lambda: test_settings

        try:
            client = TestClient(app)

            response = client.post("/ingest", json={"force_rebuild": True})

            # Must return 400 (bad request) for empty directory
            assert response.status_code == 400, (
                f"Expected 400 for empty directory, got {response.status_code}"
            )

            # Error message should be informative
            assert "No markdown files" in response.text or "markdown files found" in response.text

        finally:
            app.dependency_overrides.clear()
