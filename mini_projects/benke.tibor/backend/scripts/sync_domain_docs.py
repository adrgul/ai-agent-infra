#!/usr/bin/env python3
"""
Universal document sync script for any domain (HR, IT, Finance, Marketing, etc.).

This script:
1. Downloads all files from a specified Google Drive folder
2. Extracts text content (PDF, DOCX)
3. Chunks the text into manageable pieces
4. Generates embeddings using OpenAI
5. Stores in Qdrant with domain metadata for filtering

Usage:
    python backend/scripts/sync_domain_docs.py --domain hr --folder-id FOLDER_ID
    python backend/scripts/sync_domain_docs.py --domain it --folder-id FOLDER_ID
    python backend/scripts/sync_domain_docs.py --domain marketing --folder-id 1Jo5doFrRgTscczqR0c6bsS2H0a7pS2ZR

Domain metadata enables:
- Hybrid search (semantic + lexical)
- Domain-specific filtering (only search HR docs for HR queries)
- Multi-domain knowledge base in single Qdrant collection
"""
import os
import sys
import logging
import argparse
from pathlib import Path
from typing import List, Dict
import hashlib
from datetime import datetime

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

# Third-party imports
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Local imports
from infrastructure.google_drive_client import get_drive_client
from infrastructure.document_parser import DocumentParser
from infrastructure.openai_clients import OpenAIClientFactory

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
COLLECTION_NAME = "multi_domain_kb"  # Single collection for all domains
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))

# Valid domains
VALID_DOMAINS = ["hr", "it", "finance", "legal", "marketing", "general"]


class DomainDocsSync:
    """Sync documents from Google Drive to Qdrant with domain metadata."""
    
    def __init__(self, domain: str):
        """
        Initialize clients.
        
        Args:
            domain: Domain type (hr, it, finance, marketing, etc.)
        """
        if domain.lower() not in VALID_DOMAINS:
            raise ValueError(f"Invalid domain '{domain}'. Valid: {VALID_DOMAINS}")
        
        self.domain = domain.lower()
        self.drive_client = get_drive_client()
        self.qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        # Use centralized embeddings factory
        self.embeddings = OpenAIClientFactory.get_embeddings()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
    def ensure_collection_exists(self) -> None:
        """Create multi-domain collection if it doesn't exist."""
        try:
            collections = self.qdrant_client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if COLLECTION_NAME in collection_names:
                logger.info(f"Collection '{COLLECTION_NAME}' already exists")
                return
            
            # Create collection with OpenAI embedding dimensions
            logger.info(f"Creating multi-domain collection '{COLLECTION_NAME}'")
            self.qdrant_client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=1536,  # text-embedding-3-small dimension
                    distance=Distance.COSINE
                )
            )
            
            # Create payload index for domain filtering (important for performance!)
            self.qdrant_client.create_payload_index(
                collection_name=COLLECTION_NAME,
                field_name="domain",
                field_schema="keyword"
            )
            
            logger.info(f"✅ Collection '{COLLECTION_NAME}' created with domain index")
            
        except Exception as e:
            logger.error(f"Failed to create collection: {e}")
            raise
    
    def download_and_parse_file(self, file_id: str, file_name: str, mime_type: str) -> str:
        """
        Download and parse a single file.
        
        Args:
            file_id: Google Drive file ID
            file_name: File name for logging
            mime_type: MIME type
        
        Returns:
            Extracted text content
        """
        try:
            logger.info(f"📥 Downloading: {file_name}")
            content = self.drive_client.download_file_content(file_id)
            
            logger.info(f"📄 Parsing: {file_name} ({mime_type})")
            text = DocumentParser.parse_document(content, mime_type)
            
            logger.info(f"✅ Extracted {len(text)} characters from {file_name}")
            return text
            
        except Exception as e:
            logger.error(f"❌ Failed to process {file_name}: {e}")
            raise
    
    def chunk_text(self, text: str, source_metadata: Dict) -> List[Dict]:
        """
        Split text into chunks with domain metadata.
        
        Args:
            text: Full text content
            source_metadata: File metadata (name, id, etc.)
        
        Returns:
            List of chunk dictionaries with text and metadata
        """
        chunks = self.text_splitter.split_text(text)
        
        chunk_dicts = []
        for i, chunk in enumerate(chunks):
            chunk_dict = {
                "text": chunk,
                "metadata": {
                    "source_file_id": source_metadata["id"],
                    "source_file_name": source_metadata["name"],
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "domain": self.domain,  # Domain metadata for filtering
                    "indexed_at": datetime.utcnow().isoformat()
                }
            }
            chunk_dicts.append(chunk_dict)
        
        logger.info(f"✂️  Split into {len(chunks)} chunks (domain={self.domain})")
        return chunk_dicts
    
    def generate_embeddings(self, chunks: List[Dict]) -> List[Dict]:
        """
        Generate embeddings for all chunks.
        
        Args:
            chunks: List of chunk dictionaries
        
        Returns:
            Chunks with embeddings added
        """
        texts = [chunk["text"] for chunk in chunks]
        
        logger.info(f"🧠 Generating embeddings for {len(texts)} chunks...")
        embeddings = self.embeddings.embed_documents(texts)
        
        for chunk, embedding in zip(chunks, embeddings):
            chunk["embedding"] = embedding
        
        logger.info(f"✅ Generated {len(embeddings)} embeddings")
        return chunks
    
    def upsert_to_qdrant(self, chunks: List[Dict]) -> None:
        """
        Upload chunks to Qdrant with domain metadata.
        
        Args:
            chunks: List of chunk dictionaries with embeddings
        """
        points = []
        for chunk in chunks:
            # Generate unique ID from domain + file + chunk index
            point_id = hashlib.md5(
                f"{self.domain}_{chunk['metadata']['source_file_id']}_{chunk['metadata']['chunk_index']}".encode()
            ).hexdigest()
            
            point = PointStruct(
                id=point_id,
                vector=chunk["embedding"],
                payload={
                    "text": chunk["text"],
                    **chunk["metadata"]  # Includes domain field
                }
            )
            points.append(point)
        
        logger.info(f"⬆️  Uploading {len(points)} points to Qdrant (domain={self.domain})...")
        self.qdrant_client.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )
        logger.info(f"✅ Uploaded {len(points)} points")
    
    def sync_file(self, file_metadata: Dict) -> None:
        """
        Sync a single file to Qdrant.
        
        Args:
            file_metadata: File metadata from Google Drive
        """
        file_id = file_metadata["id"]
        file_name = file_metadata["name"]
        mime_type = file_metadata["mimeType"]
        
        logger.info(f"\n{'='*60}")
        logger.info(f"📁 Processing: {file_name} (domain={self.domain})")
        logger.info(f"{'='*60}")
        
        try:
            # Download and parse
            text = self.download_and_parse_file(file_id, file_name, mime_type)
            
            # Chunk with domain metadata
            chunks = self.chunk_text(text, file_metadata)
            
            # Generate embeddings
            chunks_with_embeddings = self.generate_embeddings(chunks)
            
            # Upload to Qdrant
            self.upsert_to_qdrant(chunks_with_embeddings)
            
            logger.info(f"✅ Successfully synced: {file_name}")
            
        except Exception as e:
            logger.error(f"❌ Failed to sync {file_name}: {e}")
            raise
    
    def sync_folder(self, folder_id: str) -> None:
        """
        Sync all documents from a Google Drive folder.
        
        Args:
            folder_id: Google Drive folder ID
        """
        logger.info(f"\n🚀 Starting Domain Documents Sync")
        logger.info(f"🏷️  Domain: {self.domain.upper()}")
        logger.info(f"📂 Google Drive Folder: {folder_id}")
        logger.info(f"🗄️  Qdrant Collection: {COLLECTION_NAME}")
        logger.info(f"📊 Qdrant: {QDRANT_HOST}:{QDRANT_PORT}\n")
        
        # Authenticate Google Drive
        if not self.drive_client.service:
            logger.info("🔐 Authenticating with Google Drive...")
            self.drive_client.authenticate()
        
        # Ensure collection exists
        self.ensure_collection_exists()
        
        # List files
        logger.info("\n📋 Listing files from Google Drive...")
        files = self.drive_client.list_files_in_folder(folder_id)
        logger.info(f"Found {len(files)} files")
        
        # Filter supported file types
        supported_types = [
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/msword"
        ]
        
        files_to_sync = [
            f for f in files 
            if f.get("mimeType") in supported_types
        ]
        
        logger.info(f"📌 {len(files_to_sync)} files to sync (PDF/DOCX only)")
        
        # Sync each file
        success_count = 0
        error_count = 0
        
        for file_metadata in files_to_sync:
            try:
                self.sync_file(file_metadata)
                success_count += 1
            except Exception as e:
                logger.error(f"Skipping file due to error: {e}")
                error_count += 1
                continue
        
        # Summary
        logger.info(f"\n{'='*60}")
        logger.info(f"🎉 Sync Complete for {self.domain.upper()} Domain!")
        logger.info(f"{'='*60}")
        logger.info(f"✅ Success: {success_count} files")
        logger.info(f"❌ Errors: {error_count} files")
        
        # Get collection info
        collection_info = self.qdrant_client.get_collection(COLLECTION_NAME)
        logger.info(f"📊 Total points in collection: {collection_info.points_count}")
        
        # Count points for this domain
        domain_count = self.qdrant_client.count(
            collection_name=COLLECTION_NAME,
            count_filter={
                "must": [
                    {
                        "key": "domain",
                        "match": {"value": self.domain}
                    }
                ]
            }
        )
        logger.info(f"📊 Points for {self.domain.upper()} domain: {domain_count.count}")


def main():
    """Main entry point with CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Sync domain-specific documents from Google Drive to Qdrant"
    )
    parser.add_argument(
        "--domain",
        type=str,
        required=True,
        choices=VALID_DOMAINS,
        help="Domain type (hr, it, finance, marketing, etc.)"
    )
    parser.add_argument(
        "--folder-id",
        type=str,
        required=True,
        help="Google Drive folder ID containing domain documents"
    )
    
    args = parser.parse_args()
    
    try:
        syncer = DomainDocsSync(domain=args.domain)
        syncer.sync_folder(folder_id=args.folder_id)
    except KeyboardInterrupt:
        logger.info("\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
