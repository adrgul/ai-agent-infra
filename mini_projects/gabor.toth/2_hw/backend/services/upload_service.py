"""Upload service for document processing."""

import uuid
import unicodedata
import asyncio
from datetime import datetime
from typing import List, Optional

from domain.models import Chunk, UploadedDocument, Message, MessageRole
from domain.interfaces import (
    DocumentTextExtractor, Chunker, EmbeddingService, VectorStore,
    UploadRepository, UserProfileRepository, ActivityCallback
)
from infrastructure.extractors import get_extractor


class UploadService:
    """Service for handling document uploads and indexing."""

    @staticmethod
    def _slugify_collection_name(text: str) -> str:
        """
        Convert category name to valid ChromaDB collection slug.
        Only alphanumeric, underscore, hyphen allowed.
        Must be 3-63 chars, start/end with alphanumeric.
        """
        # Normalize unicode chars to ASCII (é -> e, etc.)
        text = unicodedata.normalize('NFKD', text)
        text = text.encode('ascii', 'ignore').decode('ascii')
        
        # Lowercase and replace spaces/slashes with underscore
        text = text.lower().replace(" ", "_").replace("/", "_")
        
        # Remove non-alphanumeric except underscore and hyphen
        text = ''.join(c if c.isalnum() or c in '_-' else '' for c in text)
        
        # Trim underscores/hyphens from start/end
        text = text.strip('_-')
        
        # Ensure minimum 3 chars
        if len(text) < 3:
            text = text + 'x' * (3 - len(text))
        
        # Truncate if too long
        if len(text) > 63:
            text = text[:63]
        
        return text

    def __init__(
        self,
        chunker: Chunker,
        embedding_service: EmbeddingService,
        vector_store: VectorStore,
        upload_repo: UploadRepository,
        profile_repo: UserProfileRepository,
        activity_callback: Optional[ActivityCallback] = None,
    ):
        self.chunker = chunker
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.upload_repo = upload_repo
        self.profile_repo = profile_repo
        self.activity_callback = activity_callback

    async def process_upload(
        self,
        filename: str,
        content: bytes,
        category: str,
        chunk_size_tokens: int = 900,
        overlap_tokens: int = 150,
        embedding_batch_size: int = 100,
    ) -> UploadedDocument:
        """
        Process uploaded document: extract, chunk, embed, index.
        Note: Embedding and indexing may run asynchronously in background.
        Uploads are shared across all users (not tied to user_id).
        """
        # Generate upload ID
        upload_id = str(uuid.uuid4())

        # Validate category
        category = category.strip()
        if not category:
            raise ValueError("Category cannot be empty")

        # Save upload file
        file_path = self.upload_repo.save_upload(
            category, upload_id, filename, content
        )

        # Return immediately with success, schedule embedding/indexing in background
        # This ensures fast response to user
        asyncio.create_task(
            self._embed_and_index(
                category, upload_id, filename, file_path,
                chunk_size_tokens, overlap_tokens, embedding_batch_size
            )
        )

        return UploadedDocument(
            upload_id=upload_id,
            user_id="shared",  # Mark as shared across all users
            filename=filename,
            category=category,
            size=len(content),
            created_at=datetime.now(),
            chunk_size_tokens=chunk_size_tokens,
            overlap_tokens=overlap_tokens,
            embedding_batch_size=embedding_batch_size,
        )

    async def _embed_and_index(
        self,
        category: str,
        upload_id: str,
        filename: str,
        file_path: str,
        chunk_size_tokens: int,
        overlap_tokens: int,
        embedding_batch_size: int,
    ) -> None:
        """Background task to embed and index document."""
        try:
            # Log: Upload start
            if self.activity_callback:
                await self.activity_callback.log_activity(
                    f"📄 Dokumentum feldolgozása: {filename}",
                    activity_type="processing"
                )

            # Get extractor and extract text
            extractor = get_extractor(filename)
            text = await extractor.extract_text(file_path)
            text_char_count = len(text)

            # Log: Text extraction completed
            if self.activity_callback:
                await self.activity_callback.log_activity(
                    f"📖 Szöveg kinyerése: {text_char_count:,} karakter",
                    activity_type="success"
                )

            # Chunk text
            chunk_texts = self.chunker.chunk_text(
                text, chunk_size_tokens, overlap_tokens
            )
            chunk_count = len(chunk_texts)
            avg_chars = text_char_count // max(1, chunk_count)

            # Log: Chunking completed
            if self.activity_callback:
                await self.activity_callback.log_activity(
                    f"✂️ Chunkolás kész: {chunk_count} darab, átlag {avg_chars:,} karakter/chunk",
                    activity_type="success",
                    metadata={"chunk_count": chunk_count, "avg_chars": avg_chars}
                )

            # Create Chunk objects
            chunks = []
            for i, chunk_text in enumerate(chunk_texts):
                chunk = Chunk(
                    chunk_id=f"{upload_id}:{i}",
                    content=chunk_text,
                    upload_id=upload_id,
                    category=category,
                    source_file=filename,
                    chunk_index=i,
                    start_char=0,  # Simplified for now
                    end_char=len(chunk_text),
                    metadata={
                        "chunk_size_tokens": chunk_size_tokens,
                        "overlap_tokens": overlap_tokens,
                    }
                )
                chunks.append(chunk)

            # Log: Embedding start
            if self.activity_callback:
                await self.activity_callback.log_activity(
                    f"🔗 Embedding feldolgozása: {chunk_count} chunk, {len(chunk_texts) // max(1, embedding_batch_size) + 1} batch",
                    activity_type="processing",
                    metadata={"chunk_count": chunk_count, "batch_size": embedding_batch_size}
                )

            # Embed chunks
            texts_to_embed = [chunk.content for chunk in chunks]
            embeddings = await self.embedding_service.embed_texts(
                texts_to_embed, embedding_batch_size
            )

            # Log: Embedding completed
            if self.activity_callback:
                await self.activity_callback.log_activity(
                    f"✓ Embedding kész: {len(embeddings)} vektor",
                    activity_type="success",
                    metadata={"embedding_count": len(embeddings)}
                )

            # Get collection name (slugified for ChromaDB) - no user_id
            category_slug = self._slugify_collection_name(category)
            collection_name = f"cat_{category_slug}"

            # Log: Vector indexing start
            if self.activity_callback:
                await self.activity_callback.log_activity(
                    f"📊 Vektor-indexelés: '{collection_name}' kollekció",
                    activity_type="processing"
                )

            # Add to vector store with embeddings
            await self.vector_store.add_chunks(collection_name, chunks, embeddings)

            # Save chunks to disk
            await self.upload_repo.save_chunks(category, upload_id, chunks)

            # Log: Complete success
            if self.activity_callback:
                await self.activity_callback.log_activity(
                    f"✅ Feltöltés kész: {upload_id}",
                    activity_type="success",
                    metadata={"upload_id": upload_id, "chunk_count": chunk_count}
                )

            print(f"✅ Background indexing completed for {upload_id}")
        except Exception as e:
            # Log: Error
            if self.activity_callback:
                await self.activity_callback.log_activity(
                    f"❌ Feltöltés hiba: {str(e)[:100]}",
                    activity_type="error",
                    metadata={"error": str(e)}
                )
            print(f"❌ Background indexing failed for {upload_id}: {e}")
            import traceback
            traceback.print_exc()

    async def delete_upload(
        self,
        category: str,
        upload_id: str,
        filename: str,
    ) -> None:
        """Delete upload and remove vectors from category collection."""
        # Get chunks to know which IDs to delete
        chunks = await self.upload_repo.load_chunks(category, upload_id)
        chunk_ids = [chunk.chunk_id for chunk in chunks]

        # Delete vectors
        if chunk_ids:
            category_slug = self._slugify_collection_name(category)
            collection_name = f"cat_{category_slug}"
            await self.vector_store.delete_chunks(collection_name, chunk_ids)

        # Delete files
        self.upload_repo.delete_upload(category, upload_id, filename)
