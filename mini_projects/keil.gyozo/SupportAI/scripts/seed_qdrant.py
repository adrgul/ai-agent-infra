"""Script to seed Qdrant with sample knowledge base documents.

Usage:
    python scripts/seed_qdrant.py
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.qdrant_service import QdrantService
from src.services.embedding_service import EmbeddingService
from src.utils.logging import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


# Sample knowledge base documents
SAMPLE_DOCUMENTS = [
    {
        "doc_id": "KB-1001",
        "chunk_id": "KB-1001-c-1",
        "title": "How to Handle Duplicate Charges",
        "content": (
            "Duplicate charges are typically resolved within 3-5 business days. "
            "To resolve a duplicate charge: 1) Contact support with both transaction IDs, "
            "2) We'll investigate and verify the duplicate charge, "
            "3) Refund will be processed to your original payment method. "
            "You'll receive a confirmation email once the refund is initiated."
        ),
        "url": "https://kb.company.com/billing/duplicate-charges",
        "category": "billing",
        "subcategory": "duplicate_charge",
        "doc_type": "kb_article",
        "created_at": "2025-01-15T10:00:00+00:00",
        "updated_at": "2025-01-20T14:30:00+00:00",
    },
    {
        "doc_id": "FAQ-2001",
        "chunk_id": "FAQ-2001-c-1",
        "title": "Refund Processing Timeframes",
        "content": (
            "Refunds are processed within 5-10 business days after approval. "
            "The timeline depends on your payment method and bank processing times. "
            "Credit card refunds typically appear in 3-5 days, while bank transfers "
            "may take 7-10 days. You can track your refund status in your account dashboard."
        ),
        "url": "https://kb.company.com/faq/refunds",
        "category": "billing",
        "subcategory": "refund",
        "doc_type": "faq",
        "created_at": "2025-01-10T09:00:00+00:00",
        "updated_at": "2025-01-15T11:00:00+00:00",
    },
    {
        "doc_id": "KB-3001",
        "chunk_id": "KB-3001-c-1",
        "title": "Subscription Cancellation Policy",
        "content": (
            "You can cancel your subscription at any time from your account settings. "
            "Cancellations take effect at the end of your current billing period. "
            "No refunds are provided for partial months unless there's a service outage. "
            "You'll retain access to all features until the end of your paid period."
        ),
        "url": "https://kb.company.com/billing/cancellation",
        "category": "billing",
        "subcategory": "cancellation",
        "doc_type": "kb_article",
        "created_at": "2025-01-08T12:00:00+00:00",
        "updated_at": "2025-01-22T09:00:00+00:00",
    },
    {
        "doc_id": "KB-4001",
        "chunk_id": "KB-4001-c-1",
        "title": "Technical Support Escalation Process",
        "content": (
            "For complex technical issues, our escalation process ensures proper handling: "
            "1) L1 support collects initial diagnostics and attempts basic troubleshooting, "
            "2) P1 issues escalate immediately to engineering team, "
            "3) P2 issues escalate within 4 hours if unresolved, "
            "4) Customer receives status updates every 2 hours for P1, every 4 hours for P2."
        ),
        "url": "https://kb.company.com/technical/escalation",
        "category": "technical",
        "subcategory": "escalation",
        "doc_type": "kb_article",
        "created_at": "2025-01-05T08:00:00+00:00",
        "updated_at": "2025-01-18T16:00:00+00:00",
    },
    {
        "doc_id": "KB-5001",
        "chunk_id": "KB-5001-c-1",
        "title": "Dashboard Loading Issues Troubleshooting",
        "content": (
            "If your dashboard won't load: 1) Clear browser cache and cookies, "
            "2) Try a different browser or incognito mode, "
            "3) Check if browser extensions are blocking scripts, "
            "4) Verify your internet connection is stable. "
            "If issues persist after these steps, contact support with your browser version "
            "and a screenshot of any error messages."
        ),
        "url": "https://kb.company.com/technical/dashboard-issues",
        "category": "technical",
        "subcategory": "dashboard",
        "doc_type": "kb_article",
        "created_at": "2025-01-12T14:00:00+00:00",
        "updated_at": "2025-01-19T10:00:00+00:00",
    },
    {
        "doc_id": "KB-6001",
        "chunk_id": "KB-6001-c-1",
        "title": "Password Reset Instructions",
        "content": (
            "To reset your password: 1) Click 'Forgot Password' on the login page, "
            "2) Enter your registered email address, "
            "3) Check your email for a reset link (check spam folder if not received), "
            "4) Click the link and create a new password (must be 8+ characters with uppercase, "
            "lowercase, and a number). Reset links expire after 1 hour for security."
        ),
        "url": "https://kb.company.com/account/password-reset",
        "category": "account",
        "subcategory": "password",
        "doc_type": "kb_article",
        "created_at": "2025-01-03T11:00:00+00:00",
        "updated_at": "2025-01-16T13:00:00+00:00",
    },
    {
        "doc_id": "FAQ-7001",
        "chunk_id": "FAQ-7001-c-1",
        "title": "Feature Request Submission Process",
        "content": (
            "We welcome feature requests from our users! To submit a feature request: "
            "1) Check our public roadmap to see if it's already planned, "
            "2) Submit your idea through the feedback portal in your account settings, "
            "3) Our product team reviews all requests quarterly, "
            "4) Popular requests are prioritized based on user votes and business impact. "
            "You'll receive email updates if your request is added to the roadmap."
        ),
        "url": "https://kb.company.com/product/feature-requests",
        "category": "feature_request",
        "subcategory": "submission",
        "doc_type": "faq",
        "created_at": "2025-01-06T15:00:00+00:00",
        "updated_at": "2025-01-21T11:00:00+00:00",
    },
    {
        "doc_id": "KB-8001",
        "chunk_id": "KB-8001-c-1",
        "title": "Account Access Issues",
        "content": (
            "If you can't access your account: 1) Verify you're using the correct email address, "
            "2) Try resetting your password, 3) Check if your account is locked due to "
            "multiple failed login attempts (unlocks automatically after 30 minutes), "
            "4) Ensure your subscription is active and not expired. "
            "For continued issues, contact support with your account email and registration date."
        ),
        "url": "https://kb.company.com/account/access-issues",
        "category": "account",
        "subcategory": "access",
        "doc_type": "kb_article",
        "created_at": "2025-01-09T10:00:00+00:00",
        "updated_at": "2025-01-17T14:00:00+00:00",
    },
]


async def main():
    """Seed Qdrant with sample documents."""
    logger.info("Starting Qdrant seeding process")

    # Initialize services
    qdrant_service = QdrantService()
    embedding_service = EmbeddingService()

    try:
        # Check if collection exists
        exists = await qdrant_service.collection_exists()

        if not exists:
            logger.info("Collection doesn't exist, creating...")
            vector_size = embedding_service.get_embedding_dimension()
            await qdrant_service.create_collection(vector_size=vector_size)
        else:
            logger.info("Collection already exists")

        # Generate embeddings for all documents
        logger.info(f"Generating embeddings for {len(SAMPLE_DOCUMENTS)} documents...")
        texts = [doc["content"] for doc in SAMPLE_DOCUMENTS]
        vectors = await embedding_service.embed_documents(texts)

        # Upload documents
        logger.info("Uploading documents to Qdrant...")
        await qdrant_service.upsert_documents(
            documents=SAMPLE_DOCUMENTS,
            vectors=vectors
        )

        # Verify upload
        collection_info = await qdrant_service.get_collection_info()
        logger.info(f"Collection info: {collection_info}")

        logger.info("✅ Seeding completed successfully!")
        logger.info(f"Total documents: {collection_info['points_count']}")

    except Exception as e:
        logger.error(f"❌ Seeding failed: {e}", exc_info=True)
        sys.exit(1)

    finally:
        await qdrant_service.close()


if __name__ == "__main__":
    asyncio.run(main())
