"""Qdrant Vector Store Implementation"""

import os
import logging
from typing import List
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from domain.interfaces import VectorStoreInterface, LLMClientInterface
from domain.models import DocumentChunk, SearchResult

logger = logging.getLogger(__name__)


class QdrantVectorStore(VectorStoreInterface):
    """Qdrant vector database implementation"""
    
    def __init__(self, llm_client: LLMClientInterface):
        self.llm_client = llm_client
        
        # Qdrant konfiguráció
        host = os.getenv("QDRANT_HOST", "localhost")
        port = int(os.getenv("QDRANT_PORT", "6333"))
        self.collection_name = os.getenv("QDRANT_COLLECTION", "knowledge_base")
        
        # Kapcsolódás
        self.client = QdrantClient(host=host, port=port)
        
        # Kollekcio létrehozása
        self._initialize_collection()
        
        logger.info(f"Qdrant Vector Store inicializálva - {host}:{port}")
    
    def _initialize_collection(self):
        """Kollekcio létrehozása ha még nem létezik"""
        
        collections = self.client.get_collections().collections
        collection_names = [col.name for col in collections]
        
        if self.collection_name not in collection_names:
            logger.info(f"Kollekcio létrehozása: {self.collection_name}")
            
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=3072,  # text-embedding-3-large
                    distance=Distance.COSINE
                )
            )
        else:
            logger.info(f"Kollekcio már létezik: {self.collection_name}")
    
    def add_chunks(self, chunks: List[DocumentChunk]) -> None:
        """Chunk-ok hozzáadása a vector store-hoz"""
        
        if not chunks:
            logger.warning("Nincs chunk a hozzáadáshoz")
            return
        
        logger.info(f"Chunk-ok hozzáadása: {len(chunks)} darab")
        
        points = []
        for i, chunk in enumerate(chunks):
            # Embedding generálás
            embedding = self.llm_client.generate_embedding(chunk.content)
            
            # Point létrehozása
            point = PointStruct(
                id=hash(f"{chunk.domain}_{chunk.source}_{chunk.chunk_id}") & 0x7FFFFFFF,
                vector=embedding,
                payload={
                    "content": chunk.content,
                    "domain": chunk.domain,
                    "source": chunk.source,
                    "chunk_id": chunk.chunk_id,
                    **chunk.metadata
                }
            )
            points.append(point)
            
            if (i + 1) % 10 == 0:
                logger.info(f"  Feldolgozva: {i + 1}/{len(chunks)}")
        
        # Batch upsert
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        
        logger.info(f"✓ {len(chunks)} chunk sikeresen hozzáadva")
    
    def search(self, query: str, top_k: int = 5) -> List[SearchResult]:
        """Szemantikus keresés"""
        
        logger.debug(f"Keresés: '{query}' (top_k={top_k})")
        
        # Query embedding
        query_embedding = self.llm_client.generate_embedding(query)
        
        # Keresés
        search_result = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=top_k
        )
        
        # Eredmények konvertálása
        results = []
        for hit in search_result:
            chunk = DocumentChunk(
                content=hit.payload["content"],
                domain=hit.payload["domain"],
                source=hit.payload["source"],
                chunk_id=hit.payload["chunk_id"],
                metadata={}
            )
            
            results.append(SearchResult(
                chunk=chunk,
                score=hit.score
            ))
        
        logger.debug(f"Találatok: {len(results)}")
        return results
    
    def get_collection_stats(self) -> dict:
        """Kollekcio statisztikák"""
        
        info = self.client.get_collection(self.collection_name)
        
        return {
            "collection": self.collection_name,
            "points_count": info.points_count,
            "status": info.status
        }

