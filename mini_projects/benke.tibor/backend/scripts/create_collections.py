"""
Create Qdrant collections for each domain.
Run once to initialize the vector database structure.

Usage:
    python backend/scripts/create_collections.py
"""
import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_collections():
    """Create Qdrant collections for all domains."""
    
    # Get settings from environment
    qdrant_host = os.getenv('QDRANT_HOST', 'localhost')
    qdrant_port = int(os.getenv('QDRANT_PORT', 6333))
    
    # Collection names
    collections = {
        'hr': 'hr_knowledge',
        'it': 'it_knowledge',
        'finance': 'finance_knowledge',
        'legal': 'legal_knowledge',
        'marketing': 'marketing_knowledge',
        'general': 'general_knowledge'
    }
    
    # text-embedding-3-small has 1536 dimensions
    vector_size = 1536
    
    try:
        # Connect to Qdrant
        client = QdrantClient(host=qdrant_host, port=qdrant_port)
        logger.info(f"Connected to Qdrant at {qdrant_host}:{qdrant_port}")
        
        # Create each collection
        for domain, collection_name in collections.items():
            try:
                # Check if collection exists
                existing = client.get_collections().collections
                if any(c.name == collection_name for c in existing):
                    logger.info(f"Collection '{collection_name}' already exists, skipping...")
                    continue
                
                # Create collection
                client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=vector_size,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"✓ Created collection: {collection_name} (domain: {domain})")
                
            except Exception as e:
                logger.error(f"Failed to create collection '{collection_name}': {e}")
        
        logger.info("\n✅ Collection setup complete!")
        logger.info(f"Created {len(collections)} collections for domains: {', '.join(collections.keys())}")
        
    except Exception as e:
        logger.error(f"Failed to connect to Qdrant: {e}")
        logger.error("Make sure Qdrant is running:")
        logger.error("  Docker: docker run -p 6333:6333 qdrant/qdrant")
        logger.error("  Or set QDRANT_HOST and QDRANT_PORT environment variables")
        sys.exit(1)


if __name__ == "__main__":
    create_collections()
