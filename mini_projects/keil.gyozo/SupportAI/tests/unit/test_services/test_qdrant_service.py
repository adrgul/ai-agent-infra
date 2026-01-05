"""Unit tests for Qdrant service."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.services.qdrant_service import QdrantService


class TestQdrantService:
    """Test suite for Qdrant service."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_search_returns_documents(self):
        """Test vector search returns properly formatted documents."""

        mock_client = AsyncMock()
        # NOTE: query_points returns object with .points attribute
        mock_result = MagicMock()
        mock_result.points = [
            MagicMock(
                payload={
                    "doc_id": "KB-1234",
                    "chunk_id": "KB-1234-c-45",
                    "title": "Test Document",
                    "content": "Test content",
                    "url": "https://example.com",
                    "category": "billing",
                    "subcategory": "duplicate_charge",
                    "doc_type": "kb_article"
                },
                score=0.89
            )
        ]
        mock_client.query_points.return_value = mock_result

        service = QdrantService(https=False)  # ⚠️ Explicit https=False
        service.client = mock_client

        results = await service.search(
            query_vector=[0.1] * 3072,
            top_k=5
        )

        assert len(results) == 1
        assert results[0]["doc_id"] == "KB-1234"
        assert results[0]["score"] == 0.89
        assert results[0]["category"] == "billing"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_search_with_category_filter(self):
        """Test that category filter is applied correctly."""

        mock_client = AsyncMock()
        mock_result = MagicMock()
        mock_result.points = []
        mock_client.query_points.return_value = mock_result

        service = QdrantService(https=False)
        service.client = mock_client

        await service.search(
            query_vector=[0.1] * 3072,
            category_filter="billing"
        )

        # Verify filter was passed to query_points
        call_args = mock_client.query_points.call_args
        assert call_args.kwargs.get("query_filter") is not None

    @pytest.mark.unit
    def test_chunk_id_to_uuid_deterministic(self):
        """Test that same chunk_id always produces same UUID."""

        chunk_id = "KB-1234-c-45"
        uuid1 = QdrantService.chunk_id_to_uuid(chunk_id)
        uuid2 = QdrantService.chunk_id_to_uuid(chunk_id)

        assert uuid1 == uuid2
        # Verify it's a valid UUID format
        assert len(uuid1) == 36
        assert uuid1.count("-") == 4

    @pytest.mark.unit
    def test_chunk_id_to_uuid_different_ids(self):
        """Test that different chunk_ids produce different UUIDs."""

        uuid1 = QdrantService.chunk_id_to_uuid("KB-1234-c-45")
        uuid2 = QdrantService.chunk_id_to_uuid("KB-5678-c-90")

        assert uuid1 != uuid2

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_health_check_returns_true_when_healthy(self):
        """Test health check on healthy connection."""

        mock_client = AsyncMock()
        mock_client.get_collections.return_value = []

        service = QdrantService(https=False)
        service.client = mock_client

        result = await service.health_check()

        assert result is True

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_health_check_returns_false_on_error(self):
        """Test health check on failed connection."""

        mock_client = AsyncMock()
        mock_client.get_collections.side_effect = Exception("Connection failed")

        service = QdrantService(https=False)
        service.client = mock_client

        result = await service.health_check()

        assert result is False

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_upsert_documents_validates_lengths(self):
        """Test that upsert validates document and vector lengths match."""

        service = QdrantService(https=False)
        service.client = AsyncMock()

        documents = [{"chunk_id": "KB-1", "content": "test"}]
        vectors = [[0.1] * 3072, [0.2] * 3072]  # Mismatch!

        with pytest.raises(ValueError, match="must match"):
            await service.upsert_documents(documents, vectors)
