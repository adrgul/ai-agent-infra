#!/usr/bin/env python3
"""
Sync Confluence IT Policy to Qdrant vector database.

This script:
1. Retrieves IT Policy page from Confluence using AtlassianClient
2. Parses sections (using BeautifulSoup)
3. Chunks each section into manageable pieces
4. Generates embeddings using OpenAI
5. Stores in Qdrant with domain='it' metadata

Usage:
    python backend/scripts/sync_confluence_it_policy.py
    python backend/scripts/sync_confluence_it_policy.py --clear  # Clear existing IT docs first

The script indexes the Confluence IT Policy page so that:
- IT domain queries use semantic search (not keyword matching)
- Citations come from Qdrant (consistent with other domains)
- Jira ticket creation is offered at the end of responses
"""
import os
import sys
import logging
import argparse
import asyncio
import hashlib
from pathlib import Path
from typing import List, Dict
from datetime import datetime

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

# Third-party imports
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Local imports
from infrastructure.atlassian_client import atlassian_client
from infrastructure.openai_clients import OpenAIClientFactory
from infrastructure.redis_client import redis_cache

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ConfluenceITPolicySync:
    """Syncs Confluence IT Policy page to Qdrant."""
    
    def __init__(self):
        """Initialize sync components."""
        self.qdrant_url = os.getenv("QDRANT_URL", "http://qdrant:6333")
        self.collection_name = os.getenv("QDRANT_COLLECTION", "multi_domain_kb")
        self.domain = "it"
        
        # Initialize clients
        self.qdrant_client = QdrantClient(url=self.qdrant_url)
        self.embedding_model = OpenAIClientFactory.get_embeddings()
        
        # Text splitter for chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=150,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        logger.info(f"✅ Initialized ConfluenceITPolicySync (collection: {self.collection_name})")
    
    async def retrieve_it_policy(self) -> Dict[str, str]:
        """Retrieve IT Policy sections from Confluence."""
        logger.info("📥 Retrieving IT Policy from Confluence...")
        
        sections = await atlassian_client.get_it_policy_content()
        
        if not sections:
            logger.error("❌ Failed to retrieve IT Policy from Confluence")
            return {}
        
        logger.info(f"✅ Retrieved {len(sections)} sections from IT Policy")
        return sections
    
    def chunk_sections(self, sections: Dict[str, str]) -> List[Dict]:
        """Chunk IT Policy sections into smaller pieces."""
        import re
        logger.info(f"📄 Chunking {len(sections)} sections...")
        
        chunks = []
        
        current_section_id = None
        for section_title, section_content in sections.items():
            # Extract section ID from section_title (e.g., [IT-KB-234])
            section_id = None
            if "[" in section_title and "]" in section_title:
                start = section_title.index("[")
                end = section_title.index("]", start)
                section_id = section_title[start+1:end]
            else:
                # Fallback: try to extract from content prefix
                import re
                match = re.search(r"\[([A-Z]+-KB-\d+)\]", section_content)
                if match:
                    section_id = match.group(1)

            # Inherit last known section_id for sub-sections with no explicit ID
            if section_id:
                current_section_id = section_id
            elif current_section_id:
                section_id = current_section_id

            # Ensure content is prefixed with section_id for downstream parsing
            if section_id and not section_content.startswith(f"[{section_id}]"):
                section_content = f"[{section_id}] {section_content}"
            
            # Chunk the section content
            # Note: section_content now includes [IT-KB-XXX] prefix from parser
            section_chunks = self.text_splitter.split_text(section_content)
            
            for i, chunk_text in enumerate(section_chunks):
                # Generate unique doc_id for each chunk
                chunk_hash = hashlib.md5(chunk_text.encode()).hexdigest()[:8]
                doc_id = f"{section_id or 'IT-SECTION'}-chunk-{i}-{chunk_hash}"
                
                chunks.append({
                    "doc_id": doc_id,
                    "title": section_title,
                    "content": chunk_text,
                    "section_id": section_id,  # Store for RAG context
                    "section_title": section_title,
                    "chunk_index": i,
                    "total_chunks": len(section_chunks),
                    "source": "confluence",
                    "confluence_page_id": atlassian_client.it_policy_page_id,
                    "confluence_url": f"{atlassian_client.base_url}/wiki/spaces/SD/pages/{atlassian_client.it_policy_page_id}"
                })
        
        logger.info(f"✅ Created {len(chunks)} chunks from {len(sections)} sections")
        return chunks
    
    async def generate_embeddings(self, chunks: List[Dict]) -> List[Dict]:
        """Generate embeddings for chunks using OpenAI."""
        logger.info(f"🧠 Generating embeddings for {len(chunks)} chunks...")
        
        texts = [chunk["content"] for chunk in chunks]
        
        # Check cache first (if redis_cache is available)
        cache_hits = 0
        embeddings = []
        texts_to_embed = []
        cached_indices = []
        
        for i, text in enumerate(texts):
            # Skip cache if redis_cache is None
            if redis_cache is not None:
                try:
                    cached_embedding = await redis_cache.get_embedding(text)
                    if cached_embedding:
                        embeddings.append(cached_embedding)
                        cached_indices.append(i)
                        cache_hits += 1
                        continue
                except Exception as e:
                    logger.warning(f"Redis cache error (skipping): {e}")
            
            # No cache hit or Redis unavailable
            texts_to_embed.append(text)
            embeddings.append(None)  # Placeholder
        
        # Generate embeddings for uncached texts
        if texts_to_embed:
            logger.info(f"🔄 Generating {len(texts_to_embed)} new embeddings...")
            new_embeddings = self.embedding_model.embed_documents(texts_to_embed)
            
            # Fill in the placeholders and cache
            embed_idx = 0
            for i in range(len(embeddings)):
                if embeddings[i] is None:
                    embeddings[i] = new_embeddings[embed_idx]
                    # Cache for future use (if Redis is available)
                    if redis_cache is not None:
                        try:
                            await redis_cache.set_embedding(texts[i], new_embeddings[embed_idx])
                        except Exception as e:
                            logger.warning(f"Redis cache write error (skipping): {e}")
                    embed_idx += 1
        
        logger.info(f"✅ Generated {len(embeddings)} embeddings (cache hits: {cache_hits}/{len(chunks)})")
        
        # Add embeddings to chunks
        for chunk, embedding in zip(chunks, embeddings):
            chunk["embedding"] = embedding
        
        return chunks
    
    def upsert_to_qdrant(self, chunks: List[Dict]) -> None:
        """Upsert chunks to Qdrant collection."""
        logger.info(f"💾 Upserting {len(chunks)} chunks to Qdrant...")
        
        # Ensure collection exists
        self._ensure_collection()
        
        # Create point structs
        points = []
        for chunk in chunks:
            point = PointStruct(
                id=hashlib.md5(chunk["doc_id"].encode()).hexdigest(),
                vector=chunk["embedding"],
                payload={
                    "doc_id": chunk["doc_id"],
                    "title": chunk["title"],
                    "content": chunk["content"],
                    "domain": self.domain,
                    "section_id": chunk.get("section_id"),
                    "section_title": chunk.get("section_title"),
                    "chunk_index": chunk["chunk_index"],
                    "total_chunks": chunk["total_chunks"],
                    "source": chunk["source"],
                    "confluence_page_id": chunk["confluence_page_id"],
                    "confluence_url": chunk["confluence_url"],
                    "indexed_at": datetime.utcnow().isoformat()
                }
            )
            points.append(point)
        
        # Batch upsert
        batch_size = 100
        for i in range(0, len(points), batch_size):
            batch = points[i:i+batch_size]
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=batch
            )
            logger.info(f"✅ Upserted batch {i//batch_size + 1}/{(len(points)-1)//batch_size + 1}")
        
        logger.info(f"✅ Successfully upserted {len(chunks)} chunks to Qdrant")
    
    def _ensure_collection(self) -> None:
        """Ensure Qdrant collection exists with correct configuration."""
        collections = self.qdrant_client.get_collections().collections
        collection_names = [c.name for c in collections]
        
        if self.collection_name not in collection_names:
            logger.info(f"📦 Creating collection: {self.collection_name}")
            self.qdrant_client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=1536,  # text-embedding-3-small dimension
                    distance=Distance.COSINE
                )
            )
            logger.info(f"✅ Collection created: {self.collection_name}")
        else:
            logger.info(f"✅ Collection already exists: {self.collection_name}")
    
    def clear_it_domain(self) -> None:
        """Clear all existing IT domain documents from Qdrant."""
        logger.info("🗑️ Clearing existing IT domain documents...")
        
        try:
            self.qdrant_client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="domain",
                            match=MatchValue(value=self.domain)
                        )
                    ]
                )
            )
            logger.info("✅ Cleared IT domain documents")
        except Exception as e:
            logger.warning(f"⚠️ Could not clear IT domain: {e}")
    
    async def sync(self, clear: bool = False) -> None:
        """Execute full sync workflow."""
        logger.info("🚀 Starting Confluence IT Policy sync...")
        
        # Clear existing IT docs if requested
        if clear:
            self.clear_it_domain()
        
        # 1. Retrieve IT Policy from Confluence
        sections = await self.retrieve_it_policy()
        if not sections:
            logger.error("❌ Sync failed: No sections retrieved")
            return
        
        # 2. Chunk sections
        chunks = self.chunk_sections(sections)
        
        # 3. Generate embeddings
        chunks_with_embeddings = await self.generate_embeddings(chunks)
        
        # 4. Upsert to Qdrant
        self.upsert_to_qdrant(chunks_with_embeddings)
        
        logger.info("✅ Confluence IT Policy sync completed successfully!")
        logger.info(f"📊 Total chunks indexed: {len(chunks_with_embeddings)}")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Sync Confluence IT Policy to Qdrant vector database"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing IT domain documents before syncing"
    )
    
    args = parser.parse_args()
    
    # Create syncer and run
    syncer = ConfluenceITPolicySync()
    await syncer.sync(clear=args.clear)


if __name__ == "__main__":
    asyncio.run(main())
