"""Pytest configuration and fixtures."""

import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient

from src.main import app
from src.config import Settings
from src.services.qdrant_service import QdrantService
from src.services.embedding_service import EmbeddingService


# Event loop for async tests
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Test settings
@pytest.fixture
def test_settings() -> Settings:
    """Get test settings."""
    return Settings(
        OPENAI_API_KEY="test-key",
        QDRANT_HOST="localhost",
        QDRANT_PORT=6333,
        QDRANT_HTTPS=False,  # ⚠️ Important for local testing!
        REDIS_URL="redis://localhost:6379",
        LOG_LEVEL="DEBUG",
        ENVIRONMENT="test"
    )


# Mock LLM responses
@pytest.fixture
def mock_llm_response():
    """Mock LLM response for triage."""
    return {
        "category": "Billing",
        "subcategory": "Duplicate Charge",
        "priority": "P2",
        "sla_hours": 24,
        "suggested_team": "Finance Team",
        "confidence": 0.92
    }


# FastAPI test client
@pytest.fixture
async def api_client() -> AsyncGenerator[AsyncClient, None]:
    """Create async HTTP client for API testing."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


# Sample ticket factory
@pytest.fixture
def ticket_factory():
    """Factory for creating test tickets."""
    from faker import Faker
    fake = Faker()

    def create_ticket(**kwargs):
        defaults = {
            "ticket_id": f"TKT-{fake.uuid4()[:8]}",
            "raw_message": fake.paragraph(),
            "customer_name": fake.name(),
            "customer_email": fake.email()
        }
        return {**defaults, **kwargs}

    return create_ticket


# Sample KB documents
@pytest.fixture
def sample_kb_documents():
    """Sample knowledge base documents for testing."""
    return [
        {
            "doc_id": "KB-1234",
            "chunk_id": "KB-1234-c-45",
            "title": "How to Handle Duplicate Charges",
            "content": (
                "Duplicate charges are typically resolved within 3-5 business days. "
                "To resolve a duplicate charge: 1) Contact support with transaction IDs, "
                "2) We'll investigate and verify the duplicate, 3) Refund will be "
                "processed to original payment method."
            ),
            "url": "https://kb.company.com/billing/duplicate-charges",
            "category": "billing",
            "subcategory": "duplicate_charge",
            "doc_type": "kb_article",
            "created_at": "2025-01-15T10:00:00+00:00",
            "updated_at": "2025-01-20T14:30:00+00:00",
        },
        {
            "doc_id": "FAQ-910",
            "chunk_id": "FAQ-910-c-12",
            "title": "Refund Processing Timeframes",
            "content": (
                "Refunds are processed within 5-10 business days after approval. "
                "The timeline depends on your payment method and bank processing times. "
                "Credit card refunds typically appear in 3-5 days, while bank transfers "
                "may take 7-10 days."
            ),
            "url": "https://kb.company.com/faq/refunds",
            "category": "billing",
            "subcategory": "refund",
            "doc_type": "faq",
            "created_at": "2025-01-10T09:00:00+00:00",
            "updated_at": "2025-01-15T11:00:00+00:00",
        },
        {
            "doc_id": "KB-567",
            "chunk_id": "KB-567-c-23",
            "title": "Technical Support Escalation Process",
            "content": (
                "For complex technical issues, our escalation process ensures proper "
                "handling: 1) L1 support collects initial diagnostics, 2) P1 issues "
                "escalate immediately to engineering, 3) P2 issues escalate within "
                "4 hours if unresolved, 4) Customer receives status updates every 2 hours."
            ),
            "url": "https://kb.company.com/technical/escalation",
            "category": "technical",
            "subcategory": "escalation",
            "doc_type": "kb_article",
            "created_at": "2025-01-05T08:00:00+00:00",
            "updated_at": "2025-01-18T16:00:00+00:00",
        }
    ]
