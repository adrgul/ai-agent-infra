"""
Ingest documents into Qdrant vector database.
Processes files from backend/data/files/{domain}/ directories.

Supported formats: PDF, TXT, MD, DOCX
Chunks documents and creates embeddings using OpenAI.

Usage:
    # Ingest all domains
    python backend/scripts/ingest_documents.py
    
    # Ingest specific domain
    python backend/scripts/ingest_documents.py --domain hr
    
    # Clear and re-ingest
    python backend/scripts/ingest_documents.py --domain it --clear
"""
import os
import sys
import argparse
from pathlib import Path
from typing import List, Dict
import logging

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Distance, VectorParams
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    UnstructuredMarkdownLoader,
    Docx2txtLoader,
    DirectoryLoader
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
import hashlib
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DocumentIngestion:
    """Document ingestion pipeline for Qdrant."""
    
    def __init__(self):
        self.qdrant_host = os.getenv('QDRANT_HOST', 'localhost')
        self.qdrant_port = int(os.getenv('QDRANT_PORT', 6333))
        self.embedding_model = os.getenv('EMBEDDING_MODEL', 'text-embedding-3-small')
        
        # Initialize clients
        self.client = QdrantClient(host=self.qdrant_host, port=self.qdrant_port)
        self.embeddings = OpenAIEmbeddings(model=self.embedding_model)
        
        # Text splitter config
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        # Domain to collection mapping
        self.collections = {
            'hr': 'hr_knowledge',
            'it': 'it_knowledge',
            'finance': 'finance_knowledge',
            'legal': 'legal_knowledge',
            'marketing': 'marketing_knowledge',
            'general': 'general_knowledge'
        }
    
    def load_documents_from_directory(self, domain: str) -> List:
        """Load all documents from domain directory."""
        data_path = backend_path / "data" / "files" / domain
        
        if not data_path.exists():
            logger.warning(f"Directory not found: {data_path}")
            return []
        
        documents = []
        
        # Load different file types
        loaders = {
            '**/*.pdf': PyPDFLoader,
            '**/*.txt': TextLoader,
            '**/*.md': UnstructuredMarkdownLoader,
            '**/*.docx': Docx2txtLoader,
        }
        
        for pattern, loader_cls in loaders.items():
            try:
                loader = DirectoryLoader(
                    str(data_path),
                    glob=pattern,
                    loader_cls=loader_cls,
                    show_progress=True
                )
                docs = loader.load()
                documents.extend(docs)
                if docs:
                    logger.info(f"Loaded {len(docs)} documents matching {pattern}")
            except Exception as e:
                logger.warning(f"Error loading {pattern}: {e}")
        
        logger.info(f"Total documents loaded for {domain}: {len(documents)}")
        return documents
    
    def process_documents(self, documents: List, domain: str) -> List[Dict]:
        """Split documents into chunks and prepare metadata."""
        if not documents:
            return []
        
        # Split into chunks
        chunks = self.text_splitter.split_documents(documents)
        logger.info(f"Split into {len(chunks)} chunks")
        
        # Prepare chunk data with metadata
        chunk_data = []
        for i, chunk in enumerate(chunks):
            # Generate unique ID for chunk
            chunk_id = hashlib.md5(
                f"{domain}_{chunk.metadata.get('source', 'unknown')}_{i}".encode()
            ).hexdigest()
            
            chunk_data.append({
                'id': chunk_id,
                'text': chunk.page_content,
                'metadata': {
                    'domain': domain,
                    'source': chunk.metadata.get('source', 'unknown'),
                    'chunk_index': i,
                    'total_chunks': len(chunks)
                }
            })
        
        return chunk_data
    
    def create_embeddings_and_upload(self, chunk_data: List[Dict], domain: str):
        """Create embeddings and upload to Qdrant."""
        collection_name = self.collections[domain]
        
        if not chunk_data:
            logger.info(f"No chunks to upload for domain: {domain}")
            return
        
        logger.info(f"Creating embeddings for {len(chunk_data)} chunks...")
        
        # Create embeddings in batches
        batch_size = 100
        points = []
        
        for i in range(0, len(chunk_data), batch_size):
            batch = chunk_data[i:i + batch_size]
            texts = [item['text'] for item in batch]
            
            try:
                # Create embeddings
                vectors = self.embeddings.embed_documents(texts)
                
                # Create points
                for j, (chunk, vector) in enumerate(zip(batch, vectors)):
                    points.append(
                        PointStruct(
                            id=chunk['id'],
                            vector=vector,
                            payload={
                                'text': chunk['text'],
                                'domain': chunk['metadata']['domain'],
                                'source': chunk['metadata']['source'],
                                'chunk_index': chunk['metadata']['chunk_index']
                            }
                        )
                    )
                
                logger.info(f"Processed batch {i//batch_size + 1}/{(len(chunk_data)-1)//batch_size + 1}")
                
            except Exception as e:
                logger.error(f"Error creating embeddings for batch: {e}")
                continue
        
        # Upload to Qdrant
        if points:
            try:
                self.client.upsert(
                    collection_name=collection_name,
                    points=points
                )
                logger.info(f"✓ Uploaded {len(points)} points to collection '{collection_name}'")
            except Exception as e:
                logger.error(f"Failed to upload to Qdrant: {e}")
    
    def clear_collection(self, domain: str):
        """Clear all points from a collection."""
        collection_name = self.collections[domain]
        try:
            # Delete and recreate collection
            self.client.delete_collection(collection_name)
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
            )
            logger.info(f"Cleared collection: {collection_name}")
        except Exception as e:
            logger.error(f"Failed to clear collection: {e}")
    
    def ingest_domain(self, domain: str, clear: bool = False):
        """Full ingestion pipeline for a domain."""
        logger.info(f"\n{'='*60}")
        logger.info(f"Ingesting domain: {domain}")
        logger.info(f"{'='*60}")
        
        # Clear if requested
        if clear:
            self.clear_collection(domain)
        
        # Load documents
        start_time = time.time()
        documents = self.load_documents_from_directory(domain)
        
        if not documents:
            logger.warning(f"No documents found for domain: {domain}")
            logger.info(f"Add files to: backend/data/files/{domain}/")
            return
        
        # Process documents
        chunk_data = self.process_documents(documents, domain)
        
        # Create embeddings and upload
        self.create_embeddings_and_upload(chunk_data, domain)
        
        elapsed = time.time() - start_time
        logger.info(f"✅ Domain '{domain}' ingestion complete in {elapsed:.2f}s")


def main():
    parser = argparse.ArgumentParser(description='Ingest documents into Qdrant')
    parser.add_argument('--domain', type=str, help='Specific domain to ingest (hr, it, finance, etc.)')
    parser.add_argument('--clear', action='store_true', help='Clear collection before ingestion')
    args = parser.parse_args()
    
    # Check API key
    if not os.getenv('OPENAI_API_KEY'):
        logger.error("OPENAI_API_KEY environment variable not set!")
        sys.exit(1)
    
    ingestion = DocumentIngestion()
    
    # Ingest specific domain or all
    if args.domain:
        if args.domain not in ingestion.collections:
            logger.error(f"Unknown domain: {args.domain}")
            logger.error(f"Available domains: {', '.join(ingestion.collections.keys())}")
            sys.exit(1)
        ingestion.ingest_domain(args.domain, clear=args.clear)
    else:
        # Ingest all domains
        logger.info("Ingesting all domains...")
        for domain in ingestion.collections.keys():
            ingestion.ingest_domain(domain, clear=args.clear)
    
    logger.info("\n" + "="*60)
    logger.info("✅ All ingestion tasks complete!")
    logger.info("="*60)


if __name__ == "__main__":
    main()
