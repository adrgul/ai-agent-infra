"""ChromaDB vector store implementation."""

import os
from typing import List
import chromadb

from domain.models import Chunk, RetrievedChunk
from domain.interfaces import VectorStore


class ChromaVectorStore(VectorStore):
    """Vector store using ChromaDB persistent storage."""

    def __init__(self, persist_directory: str = "data/chroma_db"):
        os.makedirs(persist_directory, exist_ok=True)
        # Use the new Chroma client API
        self.client = chromadb.PersistentClient(path=persist_directory)

    async def create_collection(self, collection_name: str) -> None:
        """Create or get a collection."""
        self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    async def add_chunks(
        self, collection_name: str, chunks: List[Chunk],
        embeddings: List[List[float]] = None
    ) -> None:
        """Add chunks to a collection with optional embeddings."""
        await self.create_collection(collection_name)
        collection = self.client.get_collection(collection_name)

        ids = [chunk.chunk_id for chunk in chunks]
        documents = [chunk.content for chunk in chunks]
        metadatas = [
            {
                "upload_id": chunk.upload_id,
                "category": chunk.category,
                "source_file": chunk.source_file,
                "chunk_index": str(chunk.chunk_index),
                "start_char": str(chunk.start_char),
                "end_char": str(chunk.end_char),
                "section_title": chunk.section_title or "",
                # Merge other metadata but exclude 'embedding' key
                **{k: v for k, v in chunk.metadata.items() if k != "embedding"},
            }
            for chunk in chunks
        ]

        # Use embeddings if provided, otherwise ChromaDB will compute them
        if embeddings:
            collection.add(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
            )
        else:
            collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
            )

    async def query(
        self, collection_name: str, query_embedding: List[float],
        top_k: int = 5, similarity_threshold: float = 0.6
    ) -> List[RetrievedChunk]:
        """Query top-k similar chunks with similarity threshold."""
        collection = self.client.get_collection(collection_name)

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
        )

        retrieved = []
        if results["ids"] and len(results["ids"]) > 0:
            for i, chunk_id in enumerate(results["ids"][0]):
                doc = results["documents"][0][i]
                distance = results["distances"][0][i]
                metadata = results["metadatas"][0][i]

                # Filter by similarity threshold
                # ChromaDB uses distance metric (lower = more similar)
                # 0.6 distance threshold filters out less relevant chunks
                if distance > similarity_threshold:
                    continue

                # Create snippet from first 200 chars
                snippet = doc[:200] + "..." if len(doc) > 200 else doc

                retrieved.append(
                    RetrievedChunk(
                        chunk_id=chunk_id,
                        content=doc,
                        distance=distance,
                        metadata=metadata,
                        snippet=snippet,
                    )
                )

        return retrieved

    async def delete_chunks(
        self, collection_name: str, chunk_ids: List[str]
    ) -> None:
        """Delete chunks by IDs."""
        collection = self.client.get_collection(collection_name)
        collection.delete(ids=chunk_ids)

    async def delete_collection(self, collection_name: str) -> None:
        """Delete an entire collection."""
        try:
            self.client.delete_collection(name=collection_name)
        except Exception as e:
            # Collection might not exist, which is fine
            print(f"Note: Collection '{collection_name}' deletion: {e}")

