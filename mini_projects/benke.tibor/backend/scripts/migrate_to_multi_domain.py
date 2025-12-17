#!/usr/bin/env python3
"""
Migrate existing 'marketing' collection to 'multi_domain_kb' with domain metadata.

This script:
1. Reads all points from the old 'marketing' collection
2. Adds 'domain': 'marketing' metadata to each point
3. Writes to new 'multi_domain_kb' collection
4. Creates domain payload index for fast filtering

Usage:
    python backend/scripts/migrate_to_multi_domain.py
"""
import os
import sys
import logging
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
OLD_COLLECTION = "marketing"
NEW_COLLECTION = "multi_domain_kb"


def migrate():
    """Migrate marketing collection to multi_domain_kb."""
    
    logger.info(f"🚀 Starting migration: {OLD_COLLECTION} → {NEW_COLLECTION}")
    logger.info(f"📊 Qdrant: {QDRANT_HOST}:{QDRANT_PORT}\n")
    
    # Connect to Qdrant
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    
    # Check if old collection exists
    collections = client.get_collections().collections
    collection_names = [c.name for c in collections]
    
    if OLD_COLLECTION not in collection_names:
        logger.error(f"❌ Collection '{OLD_COLLECTION}' not found!")
        logger.info(f"Available collections: {collection_names}")
        sys.exit(1)
    
    logger.info(f"✅ Found source collection: {OLD_COLLECTION}")
    
    # Get old collection info
    old_info = client.get_collection(OLD_COLLECTION)
    total_points = old_info.points_count
    vector_size = old_info.config.params.vectors.size
    
    logger.info(f"📊 Source collection stats:")
    logger.info(f"   - Points: {total_points}")
    logger.info(f"   - Vector size: {vector_size}")
    logger.info(f"   - Distance: {old_info.config.params.vectors.distance}\n")
    
    # Create new collection if doesn't exist
    if NEW_COLLECTION in collection_names:
        logger.warning(f"⚠️  Collection '{NEW_COLLECTION}' already exists")
        response = input("Continue and add points? (y/n): ")
        if response.lower() != 'y':
            logger.info("Aborted by user")
            sys.exit(0)
    else:
        logger.info(f"📝 Creating collection: {NEW_COLLECTION}")
        client.create_collection(
            collection_name=NEW_COLLECTION,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE
            )
        )
        
        # Create domain payload index for fast filtering
        logger.info("🔍 Creating domain payload index...")
        client.create_payload_index(
            collection_name=NEW_COLLECTION,
            field_name="domain",
            field_schema="keyword"
        )
        logger.info("✅ Domain index created\n")
    
    # Scroll through all points in old collection
    logger.info(f"📥 Reading points from {OLD_COLLECTION}...")
    
    offset = None
    migrated_count = 0
    batch_size = 100
    
    while True:
        # Scroll batch
        result = client.scroll(
            collection_name=OLD_COLLECTION,
            limit=batch_size,
            offset=offset,
            with_payload=True,
            with_vectors=True
        )
        
        points, next_offset = result
        
        if not points:
            break
        
        # Add domain metadata to each point
        new_points = []
        for point in points:
            # Copy existing payload and add domain
            new_payload = dict(point.payload) if point.payload else {}
            new_payload['domain'] = 'marketing'
            
            new_point = PointStruct(
                id=point.id,
                vector=point.vector,
                payload=new_payload
            )
            new_points.append(new_point)
        
        # Upsert to new collection
        client.upsert(
            collection_name=NEW_COLLECTION,
            points=new_points
        )
        
        migrated_count += len(new_points)
        logger.info(f"✅ Migrated {migrated_count}/{total_points} points...")
        
        # Check if we're done
        if next_offset is None:
            break
        
        offset = next_offset
    
    # Verify new collection
    new_info = client.get_collection(NEW_COLLECTION)
    logger.info(f"\n{'='*60}")
    logger.info("🎉 Migration Complete!")
    logger.info(f"{'='*60}")
    logger.info(f"📊 New collection stats:")
    logger.info(f"   - Collection: {NEW_COLLECTION}")
    logger.info(f"   - Total points: {new_info.points_count}")
    logger.info(f"   - Vector size: {new_info.config.params.vectors.size}")
    
    # Count marketing domain points
    marketing_count = client.count(
        collection_name=NEW_COLLECTION,
        count_filter={
            "must": [
                {
                    "key": "domain",
                    "match": {"value": "marketing"}
                }
            ]
        }
    )
    logger.info(f"   - Marketing domain points: {marketing_count.count}")
    
    logger.info(f"\n💡 Next steps:")
    logger.info(f"   1. Update QDRANT_COLLECTION in settings.py to '{NEW_COLLECTION}'")
    logger.info(f"   2. Restart backend: docker-compose restart backend")
    logger.info(f"   3. Test queries to verify domain filtering works")
    logger.info(f"   4. Optional: Delete old collection if migration verified")
    logger.info(f"      → client.delete_collection('{OLD_COLLECTION}')")


if __name__ == "__main__":
    try:
        migrate()
    except KeyboardInterrupt:
        logger.info("\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ Migration failed: {e}", exc_info=True)
        sys.exit(1)
