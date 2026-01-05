"""Embedding generation service using OpenAI."""

import logging
import os
from typing import List, Dict
from openai import OpenAI

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating embeddings using OpenAI."""
    
    def __init__(self):
        from .config_service import get_config_service
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        # Load from system.ini
        config = get_config_service()
        
        self.client = OpenAI(api_key=api_key)
        self.model = config.get_embedding_model()  # Now reads from OPENAI_MODEL_EMBEDDING env
        self.batch_size = config.get_embedding_batch_size()
        self.dimensions = config.get_embedding_dimensions()
        
        logger.info(
            f"EmbeddingService initialized: model={self.model}, "
            f"batch_size={self.batch_size}, dimensions={self.dimensions}"
        )
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text to embed
        
        Returns:
            Embedding vector as list of floats (3072 dimensions)
        
        Raises:
            Exception: If OpenAI API call fails
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text,
                encoding_format="float"
            )
            
            embedding = response.data[0].embedding
            
            logger.debug(f"Generated embedding: {len(embedding)} dimensions")
            
            return embedding
        
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}", exc_info=True)
            raise
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in a single API call.
        
        Args:
            texts: List of texts to embed (max batch_size items)
        
        Returns:
            List of embedding vectors
        
        Raises:
            ValueError: If texts list is too large
            Exception: If OpenAI API call fails
        """
        if len(texts) > self.batch_size:
            raise ValueError(
                f"Batch size {len(texts)} exceeds maximum {self.batch_size}"
            )
        
        if not texts or all(not t.strip() for t in texts):
            raise ValueError("Texts cannot be empty")
        
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=texts,
                encoding_format="float"
            )
            
            embeddings = [data.embedding for data in response.data]
            
            logger.info(
                f"Generated {len(embeddings)} embeddings in batch "
                f"({len(embeddings[0])} dimensions each)"
            )
            
            return embeddings
        
        except Exception as e:
            logger.error(f"Batch embedding generation failed: {e}", exc_info=True)
            raise
    
    def generate_embeddings_for_chunks(
        self,
        chunks: List[Dict]
    ) -> List[Dict]:
        """
        Generate embeddings for document chunks with batching.
        
        Args:
            chunks: List of chunk dictionaries with 'id' and 'content' keys
        
        Returns:
            List of dicts with chunk_id and embedding
            [{"chunk_id": int, "embedding": List[float]}, ...]
        
        Raises:
            Exception: If embedding generation fails
        """
        if not chunks:
            return []
        
        results = []
        total_chunks = len(chunks)
        
        logger.info(f"Generating embeddings for {total_chunks} chunks")
        
        # Process in batches
        for i in range(0, total_chunks, self.batch_size):
            batch = chunks[i:i + self.batch_size]
            batch_texts = [chunk["content"] for chunk in batch]
            batch_ids = [chunk["id"] for chunk in batch]
            
            try:
                embeddings = self.generate_embeddings_batch(batch_texts)
                
                # Combine chunk IDs with embeddings
                for chunk_id, embedding in zip(batch_ids, embeddings):
                    results.append({
                        "chunk_id": chunk_id,
                        "embedding": embedding
                    })
                
                logger.info(
                    f"Batch {i // self.batch_size + 1}: "
                    f"Processed {len(batch)} chunks "
                    f"({len(results)}/{total_chunks} total)"
                )
            
            except Exception as e:
                logger.error(
                    f"Failed to generate embeddings for batch {i // self.batch_size + 1}: {e}"
                )
                # Skip failed chunks or raise - for now, skip
                logger.warning(f"Skipping {len(batch)} chunks due to error")
                continue
        
        logger.info(
            f"Embedding generation complete: {len(results)}/{total_chunks} successful"
        )
        
        return results
